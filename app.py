import os
import discord
import asyncio
import requests
import json
import random
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCORD_TOKEN')
channel_name = os.getenv('CHANNEL_NAME')
instagram_page = os.getenv('INSTAGRAM_PAGE_URL')

################################
###### Instagram Scraping ######
################################
class InstragramScraper:
  def request_url(self, url):
    try:
      response = requests.get(url)
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

  def get_timestamp_of_last_post(self, page_url):
    response = self.request_url(page_url)
    data = self.extract_data(response)
    json_data = self.parse_data_into_json(data)
    return json_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]

#########################
###### Discord Bot ######
#########################
client = discord.Client()

async def background_task():
  await client.wait_until_ready()
  channel = discord.utils.get(client.get_all_channels(), name=channel_name)

  # initialize scraper
  timestamp_prev = 0
  scraper = InstragramScraper()

  while not client.is_closed():
    timestamp_now = scraper.get_timestamp_of_last_post(instagram_page)

    if timestamp_prev == 0:
      timestamp_prev = timestamp_now
    elif timestamp_now > timestamp_prev:
      timestamp_prev = timestamp_now
      await channel.send('new post')

    print(timestamp_prev)
    await channel.send('no new post')
    # task runs at random interval between 30 to 60 seconds
    await asyncio.sleep(random.randint(30,61))

@client.event
async def on_ready():
  print('Logged in as')
  print(client.user.name)
  print(client.user.id)
  print('------')

if __name__ == '__main__':
  client.loop.create_task(background_task())
  client.run(token)