#!/usr/bin/python

import os,sys,string

unimplementedError = 'Dbmail unimplemented'
configError = 'Dbmail configuration error'


class DbmailConfig:
    _file="/etc/dbmail/dbmail.conf"
    _config={}
    _prefix='dbmail_'
    
    def __init__(self,file=None):
        if file: self.setFile(file)
        assert(os.path.isfile(self.getFile()))
        self._parse()
        
    def setFile(self,_file): self._file=_file
    def getFile(self): return self._file

    def _parse(self):
        lines=open(self.getFile()).readlines()
        #strip cruft
        lines=map(lambda x: string.split(x,'#')[0],lines)
        lines=map(lambda x: string.strip(x),lines)
        lines=filter(lambda x: len(x)>0 and x[0] not in ('\n'),lines)
        #split stanzas and attributes
        for l in lines:
            k=v=None
            if l[0]=='[': 
                stanza=l[1:-1]
                self._config[stanza]={}
                continue
            else: 
                try:
                    k,v=string.split(l,'=',1)
                except:
                    print "[%s]" % string.split(l,'=')
                self._config[stanza][k]=v
    
    def _getConfig(self,stanza=None,key=None):
        if stanza:
            if key: 
                try:
                    return self._config[stanza][key]
                except KeyError:
                    raise configError, 'missing key [%s] for stanza [%s]' % (key,stanza)

            else: return self._config[stanza]
        return self._config

    getConfig=_getConfig
    

class Dbmail(DbmailConfig):
    _stanza_='DBMAIL'
    
    def __init__(self,file=None):
        DbmailConfig.__init__(self,file)
        self.setCursor()

    def getConfig(self,key=None):
        return self._getConfig(self._stanza_,key)

    def setCursor(self):
        storage=string.lower(self.getConfig(key='STORAGE'))
        if storage=='mysql':
            self._setMysqlDictCursor()
        elif storage=='pgsql':
            self._setPgsqlDictCursor()
        elif storage=='sqlite':
            self._setSqliteDictCursor()
        else:
            raise configError, 'invalid value for config-item: STORAGE'

    def _setMysqlDictCursor(self):
        import MySQLdb
        conn=MySQLdb.connect(host=self.getConfig('host'),user=self.getConfig('user'),
            db=self.getConfig('db'),passwd=self.getConfig('pass'))
        conn.autocommit(1)
        self._cursor=conn.cursor(MySQLdb.cursors.DictCursor)
        assert(self._cursor)

    def _setPgsqlDictCursor(self):
        use=None
        try:
            from pyPgSQL import PgSQL
            use='pgsql'
        except:
            pass
            
        try:
            import psycopg2
            import psycopg2.extras
            use='psycopg2'
        except:
            pass
            
        if use=='pgsql':
            conn = PgSQL.connect(database=self.getConfig('db'),host=self.getConfig('host'),
                user=self.getConfig('user'),password=self.getConfig('pass'))
            conn.autocommit=1
            self._conn = conn
            self._cursor = conn.cursor()
        
        elif use=='psycopg2':
            conn = psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (\
                    self.getConfig('host'), self.getConfig('user'), \
                    self.getConfig('db'), self.getConfig('pass')))
            conn.set_isolation_level(0)
            self._conn = conn
            self._cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        
        else:
            raise novalidDriver, "no postgres driver available (PgSQL or psycopg2)"

        assert(self._cursor)
            
        
    def _setSqliteDictCursor(self):
        raise unimplementedError, "sqlite dict-cursor"
        
    def getCursor(self): return self._cursor

class DbmailSmtp(Dbmail):
    _stanza_='SMTP'

class DbmailAlias(Dbmail):

    def get(self,alias,deliver_to=None):
        c=self.getCursor()
        filter=''
        q="select * from %saliases where alias=%%s" % self._prefix
        if deliver_to: 
            q="%s AND deliver_to=%%s" % q
            c.execute(q,(alias, deliver_to,))
        else:
            c.execute(q,(alias,))
        return c.fetchall()
    
    def set(self,alias,deliver_to):
        c=self.getCursor()
        q="""INSERT INTO %saliases (alias,deliver_to) VALUES (%%s,%%s)""" % self._prefix
        if not self.get(alias,deliver_to):
            assert(alias and deliver_to)
            c.execute(q, (alias,deliver_to,))
            
    def delete(self,alias,deliver_to):
        c=self.getCursor()
        q="""DELETE FROM %saliases WHERE alias=%%s AND deliver_to=%%s""" % self._prefix
        if self.get(alias,deliver_to):
            c.execute(q, (alias,deliver_to,))
            
class DbmailUser(Dbmail):
    _dirty=1
    
    def __init__(self,userid):
        Dbmail.__init__(self)
        self.setUserid(userid)
        self._userdict={}

    def create(self): pass
    def update(self): pass
    def delete(self): pass
        
    def setDirty(self,dirty=1): self._dirty=dirty
    def getDirty(self): return self._dirty
        
    def setUserid(self,userid): self._userid=userid
    def getUserid(self): return self._userid
    
    def getUserdict(self):
        if not self.getDirty() and self._userdict:
            return self._userdict
            
        q="select * from %susers where userid=%%s" % self._prefix
        c=self.getCursor()
        c.execute(q,(self.getUserid(),))
        dict = c.fetchone()
        assert(dict)
        self._userdict = dict
        self.setDirty(0)
        
        return self._userdict

    def getUidNumber(self): return self.getUserdict()['user_idnr']
    def getGidNumber(self): return self.getUserdict()['client_idnr']
    

class DbmailAutoreply(Dbmail):

    def __init__(self,userid,file=None):
        Dbmail.__init__(self,file)
        self._table="%sauto_replies" % self._prefix
        self.setUser(DbmailUser(userid))
        assert(self.getUser() != None)

    def setUser(self,user): self._user=user
    def getUser(self): return self._user

    def get(self):
        c=self.getCursor()
        q="""select reply_body from %s where user_idnr=%%s""" % self._table
        try:
            c.execute(q, (self.getUser().getUidNumber()))
            dict = c.fetchone()
            assert(dict)
        except AssertionError:
            return None
        if dict:
            return dict['reply_body']
 
    def set(self,message):
        q="""insert into %s (user_idnr,reply_body) values (%%s,%%s)""" % self._table
        self.getCursor().execute(q, (self.getUser().getUidNumber(),message,))
       
    def delete(self):
        q="""delete from %s where user_idnr=%%s""" % self._table
        self.getCursor().execute(q, (self.getUser().getUidNumber()))
    
    getReply = get
    setReply = set 
    delReply = delete
    
if __name__=='__main__':
    import unittest
    class testDbmailConfig(unittest.TestCase):
        def setUp(self):
            self.o=DbmailConfig()
            
        def testParse(self):
            self.failUnless(type(self.o._config)==type({}))
            self.failUnless(self.o._config.has_key('SMTP'))
        
        def testGetConfig(self):
            self.failUnless(self.o.getConfig())
            self.failUnless(self.o.getConfig('SMTP').has_key('SENDMAIL'))
            self.failUnless(type(int(self.o.getConfig('IMAP','NCHILDREN')))==type(1))
            
    class testDbmail(unittest.TestCase):
        def setUp(self):
            self.o=Dbmail()

        def testGetConfig(self):
            self.failUnless(self.o.getConfig().has_key('db'))

        def testSetCursor(self):
            self.o.setCursor()

    class testDbmailAlias(unittest.TestCase):
        def setUp(self):
            self.o=DbmailAlias()
            
        def testGet(self):
            self.o.set('testget','testget')
            self.failUnless(self.o.get('testget','testget'))

        def testSet(self):
            self.o.set('foo@bar','foo2@bar')
            self.failUnless(self.o.get('foo@bar'))
        
        def testDelete(self):
            self.o.set('foo2','bar2')
            self.o.delete('foo2','bar2')
            self.failIf(self.o.get('foo2','bar2'))

    class testDbmailUser(unittest.TestCase):
        def setUp(self):
            self.o = DbmailUser('testuser1')
            
        def testGet(self):
            self.failUnless(self.o.getUserdict())

        def testGetUidNumber(self):
            self.failUnless(self.o.getUidNumber())

        def testGetGidNumber(self):
            self.failUnless(self.o.getGidNumber() >= 0)

    class testDbmailAutoreply(unittest.TestCase):
        def setUp(self):
            self.o = DbmailAutoreply('testuser1')

        def testSet(self):
            self.failUnlessRaises(TypeError, self.o.set, """test '' \0  reply message""")
            self.o.set("""test '' reply message""")
            self.failUnless(self.o.get())
            self.o.delete()
            
        def testGet(self):
            self.o.set("test reply message")
            self.failUnless(self.o.get())
            self.failIf(DbmailAutoreply('testuser2').get())
            self.failIf(DbmailAutoreply('nosuchuser').get())
            
        def tearDown(self):
            try:
                self.o.delete()
            except:
                pass
                
    unittest.main() 
