class Base:
   def __init__( self, key, secret ):
      self.key_ = key
      self.secret_ = secret

   def key( self ):
      return self.key_

   def secret( self ):
      return self.secret_

Consumer = Base( XXX, XXX )
Token = Base( XXX, XXX )
