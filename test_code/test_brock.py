from functools import cached_property

import numpy as np
from pyboy.utils import WindowEvent

from pyboy_environment.environments.pokemon.pokemon_environment import (
    PokemonEnvironment,
)
from pyboy_environment.environments.pokemon import pokemon_constants as pkc
from PIL import Image

import math as mt


import cv2 as cv


class PokemonBrock(PokemonEnvironment):
    def __init__(
        self,
        act_freq: int,
        emulation_speed: int = 0,
        headless: bool = False,
    ) -> None:

        valid_actions: list[WindowEvent] = [
            WindowEvent.PRESS_ARROW_DOWN,
            WindowEvent.PRESS_ARROW_LEFT,
            WindowEvent.PRESS_ARROW_RIGHT,
            WindowEvent.PRESS_ARROW_UP,
            WindowEvent.PRESS_BUTTON_A,
            WindowEvent.PRESS_BUTTON_B,
            WindowEvent.PRESS_BUTTON_START,
        ]

        release_button: list[WindowEvent] = [
            WindowEvent.RELEASE_ARROW_DOWN,
            WindowEvent.RELEASE_ARROW_LEFT,
            WindowEvent.RELEASE_ARROW_RIGHT,
            WindowEvent.RELEASE_ARROW_UP,
            WindowEvent.RELEASE_BUTTON_A,
            WindowEvent.RELEASE_BUTTON_B,
            WindowEvent.RELEASE_BUTTON_START,
        ]

        super().__init__(
            act_freq=act_freq,
            task="brock",
            init_name="has_pokedex.state",
            emulation_speed=emulation_speed,
            valid_actions=valid_actions,
            release_button=release_button,
            headless=headless,
        )

        self.rooms = []
        self.locations = []
        self.previos_pos = [0, 0]
        self.dist_from_exit = 99
        self.distances_from_exit = []

        self.current_hp = 0
        self.current_xp = 0
        self.current_level = 0
        self.current_badges = 0
        self.current_money = 0

        self.ticks = 0
        self.x = 0
        self.y = 0

    def _get_state(self) -> np.ndarray:
        # Implement your state retrieval logic here
        game_stats = self._generate_game_stats()

        game_loaction = self._get_location()

        game_area = np.array(self.game_area()).ravel()
        
        levels = np.array(game_stats["levels"])
        type_id = np.array(game_stats["type_id"])
        hp = game_stats["hp"]
        xp = np.array(game_stats["xp"])
        badges = game_stats["badges"]
        money = game_stats["money"]
        x = game_loaction['x']
        y = game_loaction['y']
        map_id = game_loaction['map_id']

        current_hp = np.array(hp['current']).sum()

        


        array_one = np.array([levels[0], type_id[0], current_hp, xp[0], badges, money, x, y, map_id])

        return_array = np.concatenate((array_one, game_area))
        # print(return_array)

        return return_array

    def _calculate_reward(self, new_state: dict) -> float:

        total_score = 0
        game_loaction = self._get_location()
        game_stats = self._generate_game_stats()
        
        levels = np.array(game_stats["levels"])
        hp = game_stats["hp"]
        xp = np.array(game_stats["xp"])
        badges = np.array(game_stats["badges"])
        money = np.array(game_stats["money"])

        if (levels.sum() > self.current_level):
            total_score += 0.5
            self.current_level = levels.sum()
        
        if (np.array(hp['current']).sum() > self.current_hp):
            total_score += 0.5
            self.current_hp =np.array(hp['current']).sum()
        
        if (xp.sum() > self.current_xp):
            total_score += 0.5
            self.current_xp = xp.sum()

        if (badges.sum() > self.current_badges):
            total_score += 1
            self.current_badges = badges.sum()

        if (money.sum() > self.current_money):
            total_score += 0.5
            self.current_money = money.sum()



        x = game_loaction['x']
        y = game_loaction['y']
        map_id = game_loaction['map_id']

        if self.steps % 10 == 0:
            if x == self.x or y == self.y:
                total_score -= 2

            self.x = x
            self.y = y


        pos = mt.sqrt(mt.pow(x, 2) + mt.pow(y, 2))
        dpos_dt = pos - mt.sqrt(mt.pow(self.previos_pos[0], 2) + mt.pow(self.previos_pos[1], 2))

        if abs(dpos_dt) != 0:
            total_score += 0.5
        
        self.previos_pos = [x, y]

        if map_id not in self.rooms:
            self.rooms.append(map_id)
            total_score += 10
            self.dist_from_exit = 99

        else:
            if [x, y] not in self.locations:
                self.locations.append([x, y])
                total_score += 2

        game_area = self.game_area()

        return total_score


    def _check_if_done(self, game_stats: dict[str, any]) -> bool:
        # Setting done to true if agent beats first gym (temporary)
        return game_stats["badges"] > self.prior_game_stats["badges"]

    def _check_if_truncated(self, game_stats: dict) -> bool:
        # Implement your truncation check logic here

        # Maybe if we run out of pokeballs...? or a max step count
        if self.steps >= 1000:
            self.rooms.clear()
            self.locations.clear()
            self.current_hp = 0
            self.current_xp = 0
            self.current_level = 0
            self.current_badges = 0
            self.current_money = 0

            return True
        
        return False