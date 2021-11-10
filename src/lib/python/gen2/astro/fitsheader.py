#
# fitsheader.py -- module for creating FITS headers
#
#[ Eric Jeschke (eric@naoj.org) --
#  Last edit: Sun Apr 24 18:32:28 HST 2011
#]
#
import Bunch

class FitsHeaderParams(object):
    def __init__(self, helper, **kwdargs):
        self.helper = helper
        self.header = {}
        self.params = Bunch.Bunch(kwdargs)

    def update_keywords(self, keyDict):
        self.header.update(keyDict)

    def set_keywords(self, **kwdargs):
        self.update(kwdargs)

    def get_keyword(self, kwd):
        if not self.header.has_key(kwd):
            self.helper.deriveOne(kwd, self)

        return self.header[kwd]
    
    def get_keywords_list(self, *args):
        return map(self.get_keyword, args)

    def get_status(self, alias):
        # User is assumed to have passed in a parameter called status
        return self.params.status[alias]
    
    def get_status_list(self, *args):
        return map(self.get_status, args)

    
class FitsHeaderMaker(object):

    def __init__(self, logger):
        self.logger = logger

    def load(self, deriveList):
        self.deriveList = deriveList
        self.analyze_deriveList()

    def _mk_deriver_status(self, keyword, alias):
        if alias.startswith('!'):
            alias = alias[1:]
        def anon(p):
            val = p.get_status(alias)
            p.update_keywords({ keyword: val })
        return anon
        
    def _mk_deriver_const(self, keyword, const):
        def anon(p):
            p.update_keywords({ keyword: const })
        return anon
        
    def analyze_deriveList(self):
        statusset = set([])
        keyset = set([])
        keylist = []
        dMap = {}
        i = 0
        for rec in self.deriveList:
            keyword = rec['key']
            aliases = rec.get('dep', [])
            comment = rec.get('comment', '')
            index = rec.get('index', i)
            i += 1
            deriver = rec.get('derive', None)
            if deriver == None:
                try:
                    deriver = getattr(self, 'calc_%s' % keyword)

                except AttributeError:
                    raise Exception("No 'derive' for keyword '%s' and no calc_%s method found in object" % (
                        keyword, keyword))
            elif callable(deriver):
                pass

            elif isinstance(deriver, tuple):
                if deriver[0]== '@status':
                    deriver = self._mk_deriver_status(keyword, aliases[0])

                elif deriver[0]== '@const':
                    deriver = self._mk_deriver_const(keyword, deriver[1])

                else:
                    raise Exception("Don't understand derive=%s for keyword '%s'" % (
                        str(deriver), keyword))
            else:
                raise Exception("Don't understand derive=%s for keyword '%s'" % (
                    str(deriver), keyword))
            
            dependences = []
            for alias in aliases:
                if alias.startswith('!'):
                    statusset.add(alias[1:])
                elif ('.' in alias):
                    statusset.add(alias)
                else:
                    dependences.append(alias)

            bnch = Bunch.Bunch(keyword=keyword,
                               dependences=dependences,
                               deriver=deriver, index=index,
                               comment=comment)
            dMap[keyword] = bnch
            keylist.append(bnch)
            keyset.add(keyword)

        # Unordered set of all status aliases
        self.statusSet = statusset
        # Unordered set of fits keywords
        self.keySet = keyset
        keylist.sort(lambda x, y: cmp(x.index, y.index))
        # Ordered list of fits keywords
        self.keyList = map(lambda x: x.keyword, keylist)
        # reverse lookup map: keyword -> keyword info
        self.dMap = dMap

    def get_statusAliases(self):
        return self.statusSet

    def get_keywords(self):
        return self.keySet

    def get_keylist(self):
        return self.keyList

    def get_comment(self, kwd):
        return self.dMap[kwd].comment

    def deriveOne(self, kwd, p):
        bnch = self.dMap[kwd]

        if len(bnch.dependences) > 0:
            for dkwd in bnch.dependences:
                try:
                    p.get_keyword(dkwd)
                except KeyError:
                    self.deriveOne(dkwd, p)

        bnch.deriver(p)

    def deriveAll(self, p):
        errors = {}
        for kwd in self.keySet:
            try:
                try:
                    val = p.get_keyword(kwd)
                except KeyError:
                    self.deriveOne(kwd, p)
                    val = p.get_keyword(kwd)

            except Exception, e:
                errmsg = "Error deriving FITS keyword '%s': %s" % (
                    str(kwd), str(e))
                if self.logger:
                    self.logger.error(errmsg)
                errors[kwd] = errmsg
                        
        return errors

    def getKeywordsList(self, p):
        errors = self.deriveAll(p)

        kwdList = []
        for kwd in self.keyList:
            try:
                kwdList.append((kwd, p.get_keyword(kwd)))
            except KeyError:
                kwdList.append((kwd, 'UNKNOWN'))
                
        return (kwdlist, errors)

        
    def fillHDU(self, header, p):
        """Fills the HDU of a PyFITS compatible object (fitsheader)
        with the calculated FITS header values.
        Keyword parameters name all the items that are necessary for the
        deriver function to calculate the keywords.
        """

        status = 0
        self.deriveAll(p)
        
        for kwd in self.keyList:
            d = self.dMap[kwd]
            try:
                header.update(kwd, p.get_keyword(kwd), comment=d.comment)

            except Exception, e:
                self.logger.error("Error setting fits keyword '%s': %s" % (
                    kwd, str(e)))
                status = 1

        return status
#END
