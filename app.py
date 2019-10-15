import os
import discord
import asyncio
import requests
import json
import random
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
channel_name = os.getenv('CHANNEL_NAME')
instagram_page = os.getenv('INSTAGRAM_PAGE_URL')

################################
###### Instagram Scraping ######
################################
_user_agents = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.120 Safari/537.36'
]

class InstragramScraper:
  def __init__(self):
    self.profile_page_json = {}

  def generate_html(self, url):
    try:
      response = requests.get(url, headers={'User-Agent': random.choice(_user_agents)})
      response.raise_for_status()
    except requests.HTTPError:
      raise requests.HTTPError
    except requests.RequestException:
      raise requests.RequestException
    else:
      return response.text

  def extract_data(self, html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup

  def parse_data_into_json(self, soup):
    scripts = soup.find('body').find('script')
    # turn script data into text, stripping leading/trailing spaces, clean data 
    raw_string = scripts.text.strip().replace('window._sharedData =', '').replace(';', '')
    # decode string data into json object
    return json.loads(raw_string)

  def set_profile_page_json(self, page_url):
    response = self.generate_html(page_url)
    data = self.extract_data(response)
    json_data = self.parse_data_into_json(data)
    self.profile_page_json = json_data

  def get_timestamp_of_last_post(self):
    return self.profile_page_json["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]

  def get_account_name(self):
    return self.profile_page_json["entry_data"]["ProfilePage"][0]["graphql"]["user"]["full_name"]

  def get_post_text(self):
    return self.profile_page_json["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["edge_media_to_caption"]["edges"][0]["node"]["text"]

  def get_post_url_shortcode(self):
    return self.profile_page_json["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["shortcode"]

#########################
###### Discord Bot ######
#########################
client = discord.Client()

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  print('------')

def generate_message(scraper_obj):
  name = scraper_obj.get_account_name()
  time = datetime.fromtimestamp(scraper_obj.get_timestamp_of_last_post())
  text = scraper_obj.get_post_text()
  shortcode = scraper_obj.get_post_url_shortcode()
  nl = '\n'

  message = f"{name} posted at {time}:{nl}{text}{nl}https://www.instagram.com/p/{shortcode}"
  return message

async def background_task():
  await client.wait_until_ready()
  channel = discord.utils.get(client.get_all_channels(), name=channel_name)

  # initialize scraper
  timestamp_prev = 0
  scraper = InstragramScraper()

  # define what bot should do while online
  while not client.is_closed():
    scraper.set_profile_page_json(instagram_page)
    timestamp_now = scraper.get_timestamp_of_last_post()

    if timestamp_prev == 0:
      timestamp_prev = timestamp_now
    elif timestamp_now > timestamp_prev:
      print('New post at', datetime.now())
      timestamp_prev = timestamp_now
      await channel.send(generate_message(scraper))
    else:
      print('No new post at', datetime.now())

    # task runs at random interval between 2 to 4 minutes to help avoid detection
    await asyncio.sleep(random.randint(120, 240))


#####################################
#####################################

if __name__ == '__main__':
  client.loop.create_task(background_task())
  client.run(token)