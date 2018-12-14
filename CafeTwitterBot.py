# -*- coding: iso-8859-15 -*-

import urllib2
import datetime
import re
from bs4 import BeautifulSoup
import argparse

MENU_URL = 'http://www.aramarkcafe.com/layouts/canary_2015/locationhome.aspx?locationid=4119&pageid=20&stationID=-1'
CAL_REGEX = re.compile( r'\d+.*CAL|TBD' )

emojiMap = { 
   'noodles': '🍜',
   'soup': '🍲',
   'pasta': '🍝',
   'cutlery': '🍴',
   'sushi': '🍣',
   'burger': '🍔',
   'wing': '🍗',
   'pizza': '🍕',
   'plate': '🍛',
   'egg': '🍳',
   'rice': '🍚',
   'fish': '🐟',
   'tomato': '🍅',
   'meat': '🍖',
   'dumpling': '🍥',
}

animalEmoji = [
   '🐉',
   '🐓',
   '🐩',
   '🐋',
   '🌝',
   '🐪',
   '🐂',
   '🐏',
   '💩',
   '🐡',
]

wordMap = {
   'chicken': ( 'wing', 50 ),
   'pasta': ( 'pasta', 50 ),
   'pizza': ( 'pizza', 50 ),
   'rice': ( 'rice', 50 ),
   'sushi': ( 'sushi', 50 ),
   'salmon': ( 'fish', 50 ),
   'fish': ( 'fish', 50 ),
   'tomato': ( 'tomato', 50 ),
   'halibut': ( 'fish', 50 ),
   'hamburger': ( 'hamburger', 50 ),
   'burger': ( 'burger', 50 ),
   'chowder': ( 'soup', 50 ),
   'spaghetti': ( 'pasta', 50 ),
   'penne': ( 'pasta', 50 ),
   'beef': ( 'plate', 50 ),
   'chinese': ( 'noodles', 50 ),
   'cod': ( 'fish', 50 ),
   'pork': ( 'meat', 50 ),
   'bbq': ( 'meat', 50 ),
   'dim': ( 'dumpling', 25 ),
   'sum': ( 'dumpling', 25 ),
}

# Factory function for tweepy api class
def Tweeter():
   import tweepy
   from ApiKey import Consumer, Token
   auth = tweepy.OAuthHandler( Consumer.key() , Consumer.secret() )
   auth.set_access_token( Token.key(), Token.secret() )
   return tweepy.API( auth )

# This class prints tweets to the console
class ConsoleTweeter():
   def __init__( self ):
      pass

   def update_status( self, status=None ):
      if status:
         print status

def getMenuSections( htmlParser, today ):
   """Get a dict of menu section -> menu items for the day"""
   stations = {}
   # One column per day, plus some extra junk
   for col in htmlParser.select( 'div.foodMenuDayColumn' ):
      # Find the menu for today
      colDay = col.find( 'h1' )
      if not colDay or colDay.text.strip().lower() != today.lower():
         continue

      stationElements = col.select( '> span.stationUL' )
      menuElements = col.select( '> ul' )
      for station, menu in zip( stationElements, menuElements ):
         stationName = station.text.strip()
         items = menu.select( 'div.noNutritionalLink' )
         items = map( lambda x: x.text.strip(), items )
         # Get rid of non-menu items (calorie count, TBD text)
         items = filter( lambda x: CAL_REGEX.search( x ) is None, items )
         # Make sure items are unique
         items = set( items )
         # Don't bother creating empty sections
         if items:
            stations[ stationName ] = items

   return stations

def soupsAndOthers( menuDict ):
   """Convert a dict of {menu section -> menu items} to two sets: soups and other
      foods"""
   soups = set()
   others = set()

   for title, items in menuDict.iteritems():
      if title.lower() == 'soup':
         soups |= items
      else:
         others |= items

   return soups, others

def main( args ):
   today = datetime.date.today().strftime( '%A' )
   if today in [ 'Saturday', 'Sunday' ]:
      print 'not running on the weekends'
      exit()

   if args.debug:
      tweeter = ConsoleTweeter()
   else:
      tweeter = Tweeter()

   try:
      resp = urllib2.urlopen( MENU_URL )
   except urllib2.HTTPError as e:
      print e.code
      print e.read()
   except urllib2.URLError as e:
      print e.reason
   else:
      htmlParser = BeautifulSoup( resp.read() )
      menuData = getMenuSections( htmlParser, today )
      soups, foods = soupsAndOthers( menuData )
      emojiList = []
      for foodLine in foods:
         emojiScore = { k: 0 for k, v in emojiMap.iteritems() }
         for foodWord in foodLine.split( ' ' ):
            ( emoji, weight ) = wordMap.get( foodWord.lower(), ( None, None ) )
            if emoji:
               emojiScore[ emoji ] += weight
         maxWeight = 25 # threshold
         emojiWinner = 'cutlery'
         for ( emoji, weight ) in emojiScore.iteritems():
            if weight > maxWeight:
               maxWeight = weight
               emojiWinner =  emoji
         emojiList.append( emojiWinner )
      foods = map( lambda foodLine, emoji: unicode( emojiMap[ emoji ], 'utf-8' ) + foodLine, foods, emojiList )
      soups = map( lambda soupLine: unicode( emojiMap[ 'soup' ], 'utf-8' ) + soupLine, soups )

      # Compose tweet (s)
      charCount = 0
      lines = foods + soups
      tweets = [ '' ]
      i = 0
      for line in lines:
         if line.strip():
            chars = len( line ) + 1
            if chars + charCount > 140:
               tweets.append( '' )
               i += 1
               charCount = 0
            tweets[ i ] += line + '\n'
            charCount += chars

      if len( tweets ) > 2:
         print 'length of tweets exceeds 2 len is %d' % len( tweets )

      tweets = reversed( tweets )
      for tweet in tweets:
         tweeter.update_status( status=tweet )

if __name__ == "__main__":
   parser = argparse.ArgumentParser()
   parser.add_argument( '-d', '--debug', help='Print results instead of tweeting',
                        action='store_true' )
   args = parser.parse_args()
   main( args )
