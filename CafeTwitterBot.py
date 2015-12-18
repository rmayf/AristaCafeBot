# -*- coding: iso-8859-15 -*-

import urllib2
import datetime
import re
from bs4 import BeautifulSoup, NavigableString
import argparse
import random

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

def main( args ):
   today = datetime.date.today().strftime( '%a' )
   if today in [ 'Sat', 'Sun' ]:
      print 'not running on the weekends'
      exit()

   if args.debug:
      tweeter = ConsoleTweeter()
   else:
      tweeter = Tweeter()

   try:
      resp = urllib2.urlopen( 'http://www.aramarkcafe.com/arista' )
   except urllib2.HTTPError as e:
      print e.code
      print e.read()
   except urllib2.URLError as e:
      print e.reason
   else:
      # parse resp
      m = re.search( r'components/menu_weekly_alternate\.aspx\?locationid=(?P<locationId>\d+)&pageid=(?P<pageId>\d+)&menuid=(?P<menuId>\d+)',
                     resp.read() )
      if not m:
         # Aramark didn't post the fucking menu
         msg = random.choice( animalEmoji ) + " No menu posted today"
         tweeter.update_status( status=msg )
         exit()

      assert m.group( 'locationId' )
      assert m.group( 'pageId' )
      assert m.group( 'menuId' )
      try:
         resp = urllib2.urlopen( 'http://www.aramarkcafe.com/components/menu_weekly_alternate.aspx?locationid=%s&pageid=%s&menuid=%s'
                                  % ( m.group( 'locationId' ), m.group( 'pageId' ), m.group( 'menuId' ) ) )
      except urllib2.HTTPError as e:
         print e.code
         print e.read()
      except urllib2.URLError as e:
         print e.reason
      else:
         htmlParser = BeautifulSoup( resp.read() )
         soups = []
         foods = []
         def removeDups( list ):
            prev = []
            def f_( elem ):
               if elem in prev:
                  return False
               else:
                  prev.append( elem )
                  return True
            return filter( f_, list )
         for col in htmlParser.find_all( 'div', 'column' ):
            if col.find( 'div', 'header', text=lambda s: today in s ):
               br = col.find_all( 'br' )
               food_section = False
               for elem in br[ 1: ]:
                  if type( elem.previous_sibling ) != NavigableString:
                     food_section = True
                  elif food_section:
                     food =  unicode( elem.previous_sibling ).strip()
                     if food:
                        foods.append( food )
                  else:
                     soup =  unicode( elem.previous_sibling ).strip()
                     if soup:
                        soups.append( soup )
         def cleanupFoodString( food ):
            if '-' in food:
               return food.split( '-', 1 )[ -1 ].strip()
            else:
               return food.strip()

         foods = removeDups( map( cleanupFoodString, foods ) )
         soups = removeDups( soups )
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
