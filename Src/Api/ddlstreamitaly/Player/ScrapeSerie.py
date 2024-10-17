# 13.06.24

import sys
import logging

from typing import List, Dict


# External libraries
import httpx
from bs4 import BeautifulSoup


# Internal utilities
from Src.Util.headers import get_headers


# Logic class
from ...Template.Class.SearchType import MediaItem


# Variable
from ..costant import COOKIE


class GetSerieInfo:
    def __init__(self, dict_serie: MediaItem) -> None:
        """
        Initializes the GetSerieInfo object with default values.

        Parameters:
            - dict_serie (MediaItem): Dictionary containing series information (optional).
        """
        self.headers = {'user-agent': get_headers()}
        self.cookies = COOKIE
        self.url = dict_serie.url
        self.tv_name = None
        self.list_episodes = None

    def get_episode_number(self) -> List[Dict[str, str]]:
        """
        Retrieves the number of episodes for a specific season.

        Parameters:
            n_season (int): The season number.

        Returns:
            List[Dict[str, str]]: List of dictionaries containing episode information.
        """

        try:
            response = httpx.get(self.url + "?area=online", cookies=self.cookies, headers=self.headers, timeout=10)
            response.raise_for_status()

        except:
            logging.error(f"Insert value for [ips4_device_key, ips4_member_id, ips4_login_key] in config.json file SITE \\ ddlstreamitaly \\ cookie. Use browser debug and cookie request with a valid account, filter by DOC.")
            sys.exit(0)

        # Parse HTML content of the page
        soup = BeautifulSoup(response.text, "html.parser")

        # Get tv name 
        self.tv_name = soup.find("span", class_= "ipsType_break").get_text(strip=True)

        # Find the container of episodes for the specified season
        table_content = soup.find('div', class_='ipsMargin_bottom:half')
        list_dict_episode = []

        for episode_div in table_content.find_all('a', href=True):

            # Get text of episode
            part_name = episode_div.get_text(strip=True)

            if part_name:
                obj_episode = {
                    'name': part_name,
                    'url': episode_div['href']
                }

                list_dict_episode.append(obj_episode)
     
        self.list_episodes = list_dict_episode
        return list_dict_episode
        