import pandas as pd
from urllib.request import urlopen
from bs4 import BeautifulSoup

class BReferenceScraper:
    """ Class to scrape data from basketball-reference.com.
    """
    @staticmethod
    def players_table(url: str, output_path=None) -> pd.DataFrame:
        """Scraper for player stats tables available in basketball-reference.com

        Args:
            url (string): url of the page to scrape
            output_path (string, optional): path to save the csv. Defaults to None.
        Returns:
            pd.DataFrame: dataframe with the scraped data
        """
        html = urlopen(url)
        bs = BeautifulSoup(html, 'lxml')
        
        headers = [
            th.get_text() 
            for th in bs.find_all('tr', limit=2)[0].find_all('th')
            [1:]
        ]

        rows = bs.find_all('tr')[1:]
        rows_data = [
            [td.get_text() for td in rows[i].find_all('td')]
            for i in range(len(rows))
        ]

        df = pd.DataFrame(rows_data, columns=headers)
        # remove empty rows
        df.dropna(inplace=True)
        # adding 0 before decimal numbers
        df = df.applymap(lambda x: x.replace('.', '0.') 
                         if x.startswith('.') else x)
        # replace empty strings with 0
        df = df.replace(r'^\s*$', 0, regex=True)
        if output_path != None:
            df.to_csv(output_path, index=False)
        return df
    
    @staticmethod
    def player_headshot(player_name: str, output_path=None) -> str:
        """Scraper for player headshot available in basketball-reference.com

        Args:
            player_name (string): name of the player to scrape
        """
        from PIL import Image
        import time
        time.sleep(5)

        names = player_name.replace('-', ' ').replace("'", '').lower().split(' ')
        url = 'https://www.basketball-reference.com/players/' + names[1][0] + '/' + names[1][0:5] + names[0][0:2] + '01.html'
        print()
        print(player_name)
        print(url)
        bs = BeautifulSoup(urlopen(url), 'lxml')
        
        if "'" in player_name:
            player_name = player_name.replace("'", '/').split('/')[0]
        try:
            id_photo = 'Photo of ' + player_name
            img_url = bs.find('img', {'alt': id_photo})['src']
            img = Image.open(urlopen(img_url))
            
            if output_path != None:
                img.save(output_path)
            else:
                img.save('../data/breference/raw/headshots/' + player_name.lower().replace(' ', '_') + '.jpg')
            return img_url
        except TypeError:
            print('No headshot found')
            return None
    
class NbaScraper:
    """ Class to scrape data from the NBA official website.
    """
    @staticmethod
    def get_json_from_name(name: str, is_player=True) -> int:
        """ Get the json of a player or team from his name
        """
        from nba_api.stats.static import players, teams
        if is_player:
            nba_players = players.get_players()
            return [player for player in nba_players 
                    if player['full_name'] == name][0]
        else:
            nba_teams = teams.get_teams()
            return [team for team in nba_teams 
                    if team['full_name'] == name][0]
    
    @staticmethod
    def get_player_career(player_id: int) -> list:
        """ Get the career of a player from his id
        """
        from nba_api.stats.endpoints import playercareerstats
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        return career.get_data_frames()[0]
    
    @staticmethod
    def get_shot_data(id: int, team_ids: list[int], seasons: list[int]) -> list:
        """ Get the shot data of a player from his id and seasons
        """
        from nba_api.stats.endpoints import shotchartdetail
        df = pd.DataFrame()
        for season in seasons:
            for team in team_ids:
                shot_data = shotchartdetail.ShotChartDetail(
                    team_id=team,
                    player_id=id,
                    context_measure_simple='FGA',
                    season_nullable=season
                )
                df = pd.concat([df, shot_data.get_data_frames()[0]])
        
        return df
    
    @staticmethod
    def get_all_ids(only_active=True) -> list:
        """ Get all the ids of the players
        """
        from nba_api.stats.static import players
        nba_players = players.get_players()
        if only_active:
            return [player['id'] for player in nba_players 
                    if player['is_active']]
        return [player['id'] for player in nba_players]
    
    @staticmethod
    def get_player_headshot(id: int) -> str:
            """ Get the headshot of a player from his id
            """
            from nba_api.stats.static import players
            import requests
            import shutil
            
            url = f'https://ak-static.cms.nba.com/wp-content/uploads/headshots/nba/latest/260x190/{id}.png'
            output_path = f'../data/nba/raw/headshots/{id}.png'
            r = requests.get(url, stream=True)
            if r.status_code == 200:
                with open(output_path, 'wb') as f:
                    r.raw.decode_content = True
                    shutil.copyfileobj(r.raw, f)
    
    @staticmethod                                    
    def get_all_nba_headshots(only_active=False) -> None:
        """ Get the headshots of all the players
        """
        ids = NbaScraper.get_all_ids(only_active=only_active)
        for id in ids:
            NbaScraper.get_player_headshot(id)