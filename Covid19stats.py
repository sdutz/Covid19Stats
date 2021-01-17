'''Module to retrieve daily report about Corona Virus in Italy'''

#----------------------------------------------------------------
import wx
import re
import os
import time
import socket
import requests
import datetime
import platform
import configparser
import wx.lib.agw.hyperlink as hl
import matplotlib.pyplot as pyplot
from PIL import Image
from numpy import sum, diff
from statistics import mean
from threading import Timer
from subprocess import check_call
from collections import namedtuple
from resizeimage import resizeimage

#----------------------------------------------------------------
ver = '1.9'
conf = namedtuple('conf', 'region city pos')
oss = ['Darwin', 'Windows', 'Linux']
copy = ['pbcopy', 'clip', 'xclip']

#----------------------------------------------------------------
def is_connected():
    '''Test newtwork connection'''
    try:
        socket.create_connection(('1.1.1.1', 53))
        return True
    except OSError:
        return False

#----------------------------------------------------------------
def cleanName(name):
    '''trim unwanter chars from name'''
    return name.lower().replace(' ', '-').replace('\'', '-')


#----------------------------------------------------------------
class CovStats(): 
    '''Stats class'''
    def __init__(self):
        '''Constructor'''
        self.baseUrl = 'https://statistichecoronavirus.it'
        self.url = self.baseUrl + '/coronavirus-italia/'
        self.days = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
        base = os.path.realpath(__file__)[:-3]
        self.iniFile = base + '.ini'
        self.pic = base + '.png'
        self.respic = base + 'res.png'
        self.config = configparser.ConfigParser()

#----------------------------------------------------------------
    def getUrl(self, region, city):
        '''get url starting from current region and city'''
        if not city:
            return self.url
        elif region == 'Trentino Alto Adige':
            return self.url + 'coronavirus-pa-' + cleanName(city) +'/'
        else:
            return self.url + 'coronavirus-' + cleanName(region) + '/coronavirus-' + cleanName(city) +'/'

#----------------------------------------------------------------
    def getStats(self, region, city):
        '''retrieve values from website'''
        if not is_connected():
            return False, 'nessuna connessione di rete presente'
        try:
            page = requests.get(self.getUrl(region, city))
        except requests.exceptions.RequestException as e:
            return False, 'impossibile stabilire la connessione con la fonte\n' + str(e)
        allData = re.findall(r'data:.*', page.text, re.MULTILINE)
        if len(allData) < 4:
            return False, 'dati non disponibili per: '+ region + ' ' + city
        res = allData[9 if not city else 3]
        values = [int(x) for x in res[res.find('[') + 1 : res.find(']') - 1].split(',')]
        self.calcGraph(values)
        return True, self.calcStats(values)

#----------------------------------------------------------------
    def calcGraph(self, values):
        '''plot graph'''
        pyplot.plot(diff(values))
        pyplot.ylabel('')
        pyplot.xlabel('')
        pyplot.savefig(self.pic)
        pyplot.close()

#----------------------------------------------------------------
    def calcStats(self, values):
        '''performs stats'''
        today = datetime.date.today()
        res = self.days[today.weekday()] + ' ' + str(today.strftime('%d/%m/%Y')) + '\n'
        diff = values[-1] - values[-2]
        diff = str(diff) if diff < 0 else '+' + str(diff)
        res += str(values[-1]) + ' ultimi nuovi positivi ('  + diff + ') '
        m, M = min(values), max(values)
        if values[-1] == m:
            res += 'm'
        elif values[-1] == M:
            res += 'M'
        res += '\nstatistiche sugli ultimi ' + str(len(values)) + ' giorni:' + '\n'
        res += 'media giornaliera: ' + str(round(mean(values))) + '\n'
        res += 'minimo: ' + str(m) + ', massimo: ' + str(M) + '\n'
        return res + 'totale nuovi positivi: ' + str(sum(values))

#----------------------------------------------------------------
    def loadConfig(self):
        '''Load configuration from ini file'''
        self.config.read(self.iniFile)
        if 'General' in self.config.sections():
            pos = (int(self.config["General"]["PosX"]), int(self.config["General"]["PosY"]))
            return conf(self.config["General"]["Region"], self.config["General"]["City"], pos)
        else:
            return conf('Lombardia', 'Bergamo', None)

#----------------------------------------------------------------
    def saveConfig(self, cnf):
        '''Save configuration to ini file'''
        self.config["General"] = {}
        self.config["General"]["Region"] = cnf.region
        self.config["General"]["City"] = cnf.city
        self.config["General"]["PosX"] = str(cnf.pos[0])
        self.config["General"]["PosY"] = str(cnf.pos[1])
        with open(self.iniFile, 'w') as configFile:
            self.config.write(configFile)


#----------------------------------------------------------------
class CovWnd(wx.Frame): 
    '''Main Window class'''

    def __init__(self, parent, title):
        '''Constructor'''
        self.size = (250, 420)
        super(CovWnd, self).__init__(parent, title = title, size = self.size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.initItaly()
        self.stats = CovStats()
        self.initUI()
        self.timer, self.last = None, None
        cnf = self.stats.loadConfig()
        self.doShow(cnf.region, cnf.city)
        self.Centre() 
        if cnf.pos:
            self.SetPosition(cnf.pos)
        self.Show()

#----------------------------------------------------------------
    def initUI(self):
        '''Init of user interface'''
        defaults = dict(flag = wx.EXPAND|wx.ALL, border = 5)
        self.panel = wx.Panel(self) 
        box = wx.GridBagSizer()
        static = wx.StaticText(self.panel, label = 'Regione', style = wx.LEFT) 
        box.Add(static, pos = (0, 0), **defaults)
        self.regions = wx.Choice(self.panel, choices = list(self.italy.keys()))
        self.regions.SetToolTip('premi i per i dati di tutta Italia, d per default')
        box.Add(self.regions, pos = (0, 1), **defaults) 

        static = wx.StaticText(self.panel, label = 'Provincia', style = wx.ALIGN_LEFT)   
        box.Add(static, pos = (1, 0), **defaults)
        self.cities = wx.Choice(self.panel)
        self.cities.SetToolTip('premi f per cercare una provincia')
        box.Add(self.cities, pos = (1, 1), **defaults)

        self.result = wx.StaticText(self.panel, style = wx.ALIGN_CENTER)
        self.result.SetToolTip('premi r per aggiornare le statistiche, c per copiarne il contenuto')
        box.Add(self.result, pos = (2, 0), **defaults, span = (1, 2))
        self.graph = wx.StaticBitmap(self.panel, style = wx.ALIGN_CENTER)
        self.graph.SetToolTip('premi r per aggiornare le statistiche')
        box.Add(self.graph, pos = (3, 0), **defaults, span = (2, 2))
        lnk = hl.HyperLinkCtrl(parent = self.panel, label = 'fonte: ' + self.stats.baseUrl, URL = self.stats.url)
        box.Add(lnk, pos = (5, 0), **defaults, span = (1, 2))
        about = wx.StaticText(self.panel, style = wx.ALIGN_CENTER, label = 'Made by sdutz')
        about.SetToolTip('premi q per uscire')
        box.Add(about, pos = (6, 0), **defaults, span = (1, 2))

        self.regions.Bind(wx.EVT_CHOICE, self.OnRegions) 
        self.cities.Bind(wx.EVT_CHOICE, self.OnCities)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel.Bind(wx.EVT_CHAR, self.onKeyDown)
        self.panel.SetSizerAndFit(box)

#----------------------------------------------------------------
    def onClose(self, event):
        '''on Close event'''
        region = self.regions.GetString(self.regions.GetSelection())
        city = self.cities.GetString(self.cities.GetSelection())
        self.stats.saveConfig(conf(region, city, self.Position))
        if self.timer:
            self.timer.cancel()
        self.Destroy()
            
#----------------------------------------------------------------
    def onKeyDown(self, event):
        '''on key down event'''
        code = event.GetKeyCode()
        if code == ord('f'):
            self.onSearch()
        elif code == ord('q'):
            self.Close()
        elif code == ord('r'):
            self.showData()
        elif code == ord('i'):
            self.doShow('Italia')
        elif code == ord('d'):
            self.doShow('Lombardia', 'Bergamo')
        elif code == ord('h'):
            self.showHelp()
        elif code == ord('c'):
            self.doCopy()

#----------------------------------------------------------------
    def doCopy(self):
        idx = oss.index(platform.system())
        txt = "\"" + self.result.GetLabelText().strip() + "\""
        return check_call('echo '+ txt +'|' + copy[idx], shell=True)

#----------------------------------------------------------------
    def showHelp(self):
        '''show help message box'''
        text = 'Elenco comandi:\nf per cercare\nq per uscire\nr per ricaricare\ni per Italia\n'
        text += 'd per default\nc per copiare il risultato\nh per questa finestra'
        wx.MessageBox(text, parent=self, caption='Aiuto')

#----------------------------------------------------------------
    def doShow(self, region, city = None):
        '''show total data of Italy'''
        idx = list(self.italy.keys()).index(region)
        self.regions.SetSelection(idx)
        self.cities.SetItems(self.italy[region])
        self.cities.SetSelection(0 if not city else self.italy[region].index(city))
        self.showData()

#----------------------------------------------------------------
    def onSearch(self):
        '''search dialogs'''
        dlg = wx.TextEntryDialog(self, 'Cerca la città')
        if (dlg.ShowModal() == wx.ID_OK):
            if not self.doSearch(dlg.GetValue()):
                wx.MessageBox('Nessun risultato trovato!', parent=self, caption='Errore')
        dlg.Destroy()

#----------------------------------------------------------------
    def doSearch(self, city):
        '''perform serch of a city'''
        name = city.lower()
        for region in self.italy:
            for curr in self.italy[region]:
                if name == curr.lower():
                    self.doShow(region, curr)
                    return True
        return False

#----------------------------------------------------------------
    def initItaly(self):
        '''init of all regions and cities of Italy'''
        self.italy = {}
        self.italy["Abruzzo"]=sorted(["L'Aquila","Chieti","Pescara","Teramo"])
        self.italy["Basilicata"]=sorted(["Potenza","Matera"])
        self.italy["Calabria"]=sorted(["Reggio Calabria","Catanzaro","Crotone","Vibo Valentia","Cosenza"])
        self.italy["Campania"]=sorted(["Napoli","Avellino","Caserta","Benevento","Salerno"])
        self.italy["Emilia Romagna"]=sorted(["Bologna","Reggio Emilia","Parma","Modena","Ferrara","Forlì Cesena","Piacenza","Ravenna","Rimini"])
        self.italy["Friuli Venezia Giulia"]=sorted(["Trieste","Gorizia","Pordenone","Udine"])
        self.italy["Italia"]=[""]
        self.italy["Lazio"]=sorted(["Roma","Latina","Frosinone","Viterbo","Rieti"])
        self.italy["Liguria"]=sorted(["Genova","Imperia","La Spezia","Savona"])
        self.italy["Lombardia"]=sorted(["Milano","Bergamo","Brescia","Como","Cremona","Mantova","Monza Brianza","Pavia","Sondrio","Lodi","Lecco","Varese"])
        self.italy["Marche"]=sorted(["Ancona","Ascoli Piceno","Fermo","Macerata","Pesaro Urbino"])
        self.italy["Molise"]=sorted(["Campobasso","Isernia"])
        self.italy["Piemonte"]=sorted(["Torino","Asti","Alessandria","Cuneo","Novara","Vercelli","Verbania","Biella"])
        self.italy["Valle d'Aosta"]=["Aosta"]
        self.italy["Puglia"]=sorted(["Bari","Barletta-Andria-Trani","Brindisi","Foggia","Lecce","Taranto"])
        self.italy["Sardegna"]=sorted(["Cagliari","Sassari","Nuoro","Oristano","Sud Sardegna"])
        self.italy["Sicilia"]=sorted(["Palermo","Agrigento","Caltanissetta","Catania","Enna","Messina","Ragusa","Siracusa","Trapani"])
        self.italy["Toscana"]=sorted(["Arezzo","Massa Carrara","Firenze","Livorno","Grosseto","Lucca","Pisa","Pistoia","Prato","Siena"])
        self.italy["Trentino Alto Adige"]=sorted(["Trento","Bolzano"])
        self.italy["Umbria"]=sorted(["Perugia","Terni"])
        self.italy["Veneto"]=sorted(["Venezia","Belluno","Padova","Rovigo","Treviso","Verona","Vicenza"])

#----------------------------------------------------------------
    def OnRegions(self, event):
        '''on changed region selection'''
        self.cities.SetItems(self.italy[self.regions.GetString(self.regions.GetSelection())])
        self.cities.SetSelection(0)
        self.showData()

#----------------------------------------------------------------
    def showData(self):
        '''show all data about selected city'''
        start = time.process_time()
        region = self.regions.GetString(self.regions.GetSelection())
        city = self.cities.GetString(self.cities.GetSelection())
        ok, stat = self.stats.getStats(region, city)
        self.result.SetLabel(stat)
        if not ok:
            self.startTimer(False)
            return
        with open(self.stats.pic, 'r+b') as file, Image.open(file) as image:
            resized = resizeimage.resize_cover(image, (self.size[0] - 50, 150))
            resized.save(self.stats.respic, image.format)
        self.graph.SetBitmap(wx.Bitmap(self.stats.respic))
        print('retrieved in ' + str(time.process_time() - start) + ' s')
        self.last = time.time()
        self.panel.SetSize(self.size)
        self.panel.Fit()
        self.startTimer(True)

#----------------------------------------------------------------
    def startTimer(self, ok):
        '''start timer for background operation'''
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(60, self.showData) if not ok else Timer(30, self.checkTime)
        self.timer.start()

#----------------------------------------------------------------
    def checkTime(self):
        '''check timer for background operations'''
        self.showData() if time.time() - self.last > 21600 else self.startTimer(True)

#----------------------------------------------------------------
    def OnCities(self, event):
        '''on changed city selection'''
        self.showData()

#----------------------------------------------------------------
if __name__ == "__main__":
    '''main'''
    app = wx.App()
    CovWnd(None, 'Bilancio Covid ' + ver) 
    app.MainLoop()
