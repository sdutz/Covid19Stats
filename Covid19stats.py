'''Module to retrieve daily report about Corona Virus in Italy'''

#----------------------------------------------------------------
import wx
import re
import os
import time
import numpy
import socket
import requests
import datetime
import statistics
import configparser
import wx.lib.agw.hyperlink as hl
import matplotlib.pyplot as pyplot
from PIL import Image
from threading import Timer
from resizeimage import resizeimage

ver = '1.8'

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
#----------------------------------------------------------------
    def getUrl(self, region, city):
        if region == 'Trentino Alto Adige':
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
        res = allData[3]
        values = [int(x) for x in res[res.find('[') + 1 : res.find(']') - 1].split(',')]
        self.calcGraph(values)
        return True, self.calcStats(values)

#----------------------------------------------------------------
    def calcGraph(self, values):
        '''plot graph'''
        pyplot.plot(numpy.diff(values))
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
        res += 'media giornaliera: ' + str(round(statistics.mean(values))) + '\n'
        res += 'minimo: ' + str(m) + ', massimo: ' + str(M) + '\n'
        return res + 'totale nuovi positivi: ' + str(numpy.sum(values))

#----------------------------------------------------------------
    def loadConfig(self):
        '''Load configuration from ini file'''
        config = configparser.ConfigParser()
        config.read(self.iniFile)
        if 'General' in config.sections():
            pos = (int(config["General"]["PosX"]), int(config["General"]["PosY"]))
            return config["General"]["Region"], config["General"]["City"], pos
        else:
            return 'Lombardia', 'Bergamo', None

#----------------------------------------------------------------
    def saveConfig(self, region, city, pos):
        '''Save configuration to ini file'''
        config = configparser.ConfigParser()
        config["General"] = {}
        config["General"]["Region"] = region
        config["General"]["City"] = city
        config["General"]["PosX"] = str(pos[0])
        config["General"]["PosY"] = str(pos[1])
        with open(self.iniFile, 'w') as configFile:
            config.write(configFile)


#----------------------------------------------------------------
class CovWnd(wx.Frame): 
    '''Main Window class'''
    def __init__(self, parent, title):
        '''Constructor'''
        self.size = (250, 420)
        super(CovWnd, self).__init__(parent, title = title, size = self.size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.initItaly()
        self.stats = CovStats()
        region, city, pos = self.stats.loadConfig()
        self.initUI(region, city)
        self.timer, self.last = None, None
        self.showData()
        self.Centre() 
        if pos:
            self.SetPosition(pos)
        self.Show()

#----------------------------------------------------------------
    def initUI(self, region, city):
        '''Init of user interface'''
        self.panel = wx.Panel(self) 
        box = wx.GridBagSizer()
        regions = list(self.italy.keys())
        static = wx.StaticText(self.panel, label = 'Regione', style = wx.LEFT) 
        box.Add(static, pos = (0, 0), flag = wx.EXPAND|wx.ALL, border = 5)
        self.regions = wx.Choice(self.panel, choices = regions)
        self.regions.SetSelection(regions.index(region))
        box.Add(self.regions, pos = (0, 1), flag = wx.EXPAND|wx.ALL, border = 5) 

        static = wx.StaticText(self.panel, label = 'Provincia', style = wx.ALIGN_LEFT)   
        box.Add(static, pos = (1, 0), flag = wx.EXPAND|wx.ALL, border = 5)
        cities = list(self.italy[region])
        self.cities = wx.Choice(self.panel, choices = cities)
        self.cities.SetToolTip('premi f per cercare una provincia')
        self.cities.SetSelection(cities.index(city))
        box.Add(self.cities, pos = (1, 1), flag = wx.EXPAND|wx.ALL, border = 5)

        self.result = wx.StaticText(self.panel, style = wx.ALIGN_CENTER)
        self.result.SetToolTip('premi r per aggiornare le statistiche')
        box.Add(self.result, pos = (2, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))
        self.graph = wx.StaticBitmap(self.panel, style = wx.ALIGN_CENTER)
        self.graph.SetToolTip('premi r per aggiornare le statistiche')
        box.Add(self.graph, pos = (3, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (2, 2))
        lnk = hl.HyperLinkCtrl(parent = self.panel, label = 'fonte: ' + self.stats.baseUrl, URL = self.stats.url)
        box.Add(lnk, pos = (5, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))
        about = wx.StaticText(self.panel, style = wx.ALIGN_CENTER, label = 'Made by sdutz')
        about.SetToolTip('premi q per uscire')
        box.Add(about, pos = (6, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))

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
        self.stats.saveConfig(region, city, self.Position)
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

#----------------------------------------------------------------
    def onSearch(self):
        '''search dialogs'''
        dlg = wx.TextEntryDialog(self, 'Cerca la città')
        if (dlg.ShowModal() == wx.ID_OK):
            if not self.doSearch(dlg.GetValue()):
                wx.MessageBox('Nessun risultato trovato!', parent=self)
        dlg.Destroy()

#----------------------------------------------------------------
    def doSearch(self, city):
        '''perform serch of a city'''
        idx = 0
        for region in self.italy:
            if city in self.italy[region]:
                self.regions.SetSelection(idx)
                self.cities.SetItems(self.italy[region])
                self.cities.SetSelection(self.italy[region].index(city))
                self.showData()
                return True
            idx += 1
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
    def startTimer(self, read):
        if self.timer:
            self.timer.cancel()
        self.timer = Timer(60, self.showData) if not read else Timer(30, self.checkTime)
        self.timer.start()

#----------------------------------------------------------------
    def checkTime(self):
        self.showData() if time.time() - self.last > 21600 else self.startTimer(True)

#----------------------------------------------------------------
    def OnCities(self, event):
        self.showData()

#----------------------------------------------------------------
if __name__ == "__main__":              
    app = wx.App()
    CovWnd(None, 'Bilancio Covid ' + ver) 
    app.MainLoop()
