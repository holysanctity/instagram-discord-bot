from bs4 import BeautifulSoup
import requests
import json

class InstragramScraper:
  def request_url(self, url):
    #test the http error
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

  def get_timestamp_of_last_post(self, profile_url):
    response = self.request_url(profile_url)
    data = self.extract_data(response)
    json_data = self.parse_data_into_json(data)

    return json_data["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"][0]["node"]["taken_at_timestamp"]


if __name__ == '__main__':
  scraper = InstragramScraper()

  taken_at_timestamp = scraper.get_timestamp_of_last_post('https://www.instagram.com/cats_of_instagram/?hl=en')

  print(taken_at_timestamp)
