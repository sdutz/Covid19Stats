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
import matplotlib.pyplot as pyplot
from PIL import Image
from threading import Timer
from resizeimage import resizeimage

#----------------------------------------------------------------
def is_connected():
    '''Test newtwork connection'''
    try:
        socket.create_connection(('1.1.1.1', 53))
        return True
    except OSError:
        return False

#----------------------------------------------------------------
class CowWnd(wx.Frame): 
    '''Main Window class'''
    def __init__(self, parent, title): 
        '''Constructor'''
        self.size = (250, 420)
        super(CowWnd, self).__init__(parent, title = title, size = self.size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.initData()
        self.loadConfig()
        self.initUI()
        self.timer = None
        self.last = None
        self.showData()
        self.Centre() 
        self.Show()

#----------------------------------------------------------------
    def initData(self):
        '''Init of all data'''
        self.italy = {}
        self.initItaly()
        self.baseUrl = 'https://statistichecoronavirus.it'
        self.days = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]
        self.region = 'Lombardia'
        self.city = 'Bergamo'
        base = os.path.realpath(__file__)[:-3]
        self.iniFile = base + '.ini'
        self.pic = base + '.png'
        self.respic = base + 'res.png'

#----------------------------------------------------------------
    def initUI(self):
        '''Init of user interface'''
        self.panel = wx.Panel(self) 
        box = wx.GridBagSizer()
        regions = list(self.italy.keys())
        static = wx.StaticText(self.panel, label = 'Regione', style = wx.LEFT) 
        box.Add(static, pos = (0, 0), flag = wx.EXPAND|wx.ALL, border = 5)
        self.regions = wx.Choice(self.panel, choices = regions)
        self.regions.SetSelection(regions.index(self.region))
        box.Add(self.regions, pos = (0, 1), flag = wx.EXPAND|wx.ALL, border = 5) 

        static = wx.StaticText(self.panel, label = 'Provincia', style = wx.ALIGN_LEFT)   
        box.Add(static, pos = (1, 0), flag = wx.EXPAND|wx.ALL, border = 5)
        cities = list(self.italy[self.region])
        self.cities = wx.Choice(self.panel, choices = cities)
        self.cities.SetSelection(cities.index(self.city))
        box.Add(self.cities, pos = (1, 1), flag = wx.EXPAND|wx.ALL, border = 5)

        self.result = wx.StaticText(self.panel, style = wx.ALIGN_CENTER)
        box.Add(self.result, pos = (2, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))
        self.graph = wx.StaticBitmap(self.panel, style = wx.ALIGN_CENTER)
        box.Add(self.graph, pos = (3, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (2, 2))
        about = wx.StaticText(self.panel, style = wx.ALIGN_CENTER, label = 'fonte: ' + self.baseUrl + '\n\n' + 'Made by sdutz')
        box.Add(about, pos = (5, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))

        self.regions.Bind(wx.EVT_CHOICE, self.OnRegions) 
        self.cities.Bind(wx.EVT_CHOICE, self.OnCities)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel.Bind(wx.EVT_CHAR, self.onKeyDown)
        self.panel.SetSizerAndFit(box)

#----------------------------------------------------------------
    def onClose(self, event):
        '''on Close event'''
        self.saveConfig()
        if self.timer:
            self.timer.cancel()
        self.Destroy()
            
#----------------------------------------------------------------
    def onKeyDown(self, event):
        if event.GetKeyCode() == ord('f'):
            self.onSearch()

#----------------------------------------------------------------
    def onSearch(self):
        dlg = wx.TextEntryDialog(self, 'Cerca la città')
        if ( dlg.ShowModal() == wx.ID_OK):
            if not self.doSearch(dlg.GetValue()):
                wx.MessageBox('Nessun risultato trovato', parent=self)
        dlg.Destroy()

#----------------------------------------------------------------
    def doSearch(self, city):
        idx = 0
        for region in self.italy:
            if city in self.italy[region]:
                self.region = region
                self.city = city
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
        self.italy["Abruzzo"]=sorted(["L'Aquila","Chieti","Pescara","Teramo"])
        self.italy["Basilicata"]=sorted(["Potenza","Matera"])
        self.italy["Calabria"]=sorted(["Reggio Calabria","Catanzaro","Crotone","Vibo Valentia Marina","Cosenza"])
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
        self.italy["Sardegna"]=sorted(["Cagliari","Sassari","Nuoro","Oristano","Carbonia Iglesias","Medio Campidano","Olbia Tempio","Ogliastra"])
        self.italy["Sicilia"]=sorted(["Palermo","Agrigento","Caltanissetta","Catania","Enna","Messina","Ragusa","Siracusa","Trapani"])
        self.italy["Toscana"]=sorted(["Arezzo","Massa Carrara","Firenze","Livorno","Grosseto","Lucca","Pisa","Pistoia","Prato","Siena"])
        self.italy["Trentino Alto Adige"]=sorted(["Trento","Bolzano"])
        self.italy["Umbria"]=sorted(["Perugia","Terni"])
        self.italy["Veneto"]=sorted(["Venezia","Belluno","Padova","Rovigo","Treviso","Verona","Vicenza"])

#----------------------------------------------------------------
    def loadConfig(self):
        '''Load configuration from ini file'''
        config = configparser.ConfigParser()
        config.read(self.iniFile)
        if 'General' in config.sections():
            self.region = config["General"]["Region"]
            self.city   = config["General"]["City"]

#----------------------------------------------------------------
    def saveConfig(self):
        '''Save configuration to ini file'''
        config = configparser.ConfigParser()
        config["General"] = {}
        config["General"]["Region"] = self.regions.GetString( self.regions.GetSelection())
        config["General"]["City"] = self.cities.GetString( self.cities.GetSelection())
        with open(self.iniFile, 'w') as configFile:
            config.write(configFile)

#----------------------------------------------------------------
    def OnRegions(self, event):
        self.cities.SetItems(self.italy[self.regions.GetString(self.regions.GetSelection())])
        self.cities.SetSelection(0)
        self.showData()

#----------------------------------------------------------------
    def getValues(self):
        if not is_connected():
            self.result.SetLabel('nessuna connessione di rete presente')
            self.startTimer(False)
            return
        region = self.cleanName(self.regions.GetString(self.regions.GetSelection()))
        city = self.cleanName(self.cities.GetString(self.cities.GetSelection()))
        try:
            page = requests.get(self.baseUrl + '/coronavirus-italia/coronavirus-' + region + '/coronavirus-' + city +'/')
        except requests.exceptions.RequestException as e:
            self.result.SetLabel('impossibile stabilire la connessione con la fonte\n' + str(e))
            self.startTimer(False)
            return
        allData = re.findall(r'data:.*', page.text, re.MULTILINE)
        if len(allData) < 4:
            self.result.SetLabel('dati non disponibili per: ' + region + ' ' + city)
            self.startTimer(False)
            return
        res = allData[3]
        return [int(x) for x in res[res.find('[') + 1 : res.find(']') - 1].split(',')]

#----------------------------------------------------------------
    def setGraph(self, values):
        pyplot.plot(numpy.diff(values))
        pyplot.ylabel('')
        pyplot.xlabel('')
        pyplot.savefig(self.pic)
        pyplot.close()
        with open(self.pic, 'r+b') as file, Image.open(file) as image:
            resizeimage.resize_cover(image, [self.size[0] - 50, 150]).save(self.respic, image.format)
        self.graph.SetBitmap(wx.Bitmap(self.respic))

#----------------------------------------------------------------
    def setStats(self, values):
        today = datetime.date.today()
        res = self.days[today.weekday()] + ' ' + str(today.strftime('%d/%m/%Y')) + '\n'
        diff = values[-1] - values[-2]
        diff = str(diff) if diff < 0 else '+' + str(diff)
        res += str(values[-1]) + ' ultimi nuovi positivi ('  + diff + ')\n'
        res += 'statistiche sugli ultimi ' + str(len(values)) + ' giorni:' + '\n'
        res += 'media giornaliera: ' + str(round(statistics.mean(values))) + '\n'
        res += 'totale nuovi positivi: ' + str(numpy.sum(values)) + '\n'
        res += 'minimo: ' + str(min(values)) + ', massimo: ' + str(max(values))
        self.result.SetLabel(res)

#----------------------------------------------------------------
    def showData(self):
        '''show all data about selected city'''
        start = time.process_time()
        values = self.getValues()
        if not values:
            return
        self.setGraph(values)
        self.setStats(values)
        self.last = time.process_time()
        print('retrieved in ' + str(self.last - start) + ' s')
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
        if time.process_time() - self.last > 21600:
            self.showData()

#----------------------------------------------------------------
    def OnCities(self, event):
        self.showData()

#----------------------------------------------------------------
    def cleanName(self, name):
        return name.lower().replace(' ', '-').replace('\'', '-')

#----------------------------------------------------------------
if __name__ == "__main__":              
    app = wx.App() 
    CowWnd(None, 'Bilancio Covid') 
    app.MainLoop()
