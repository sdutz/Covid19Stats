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
from resizeimage import resizeimage

#----------------------------------------------------------------
def is_connected():
    '''Test newtwork connection'''
    try:
        socket.create_connection(("1.1.1.1", 53))
        return True
    except OSError:
        return False

#----------------------------------------------------------------
class CowWnd(wx.Frame): 
    '''Main Window class'''
    def __init__(self, parent, title): 
        '''Constructor'''
        self.size = (250, 400)
        super(CowWnd, self).__init__(parent, title = title, size = self.size, style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.initData()
        self.loadConfig()
        self.initUI()
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
        self.panel.SetSizerAndFit(box)

#----------------------------------------------------------------
    def onClose(self, event):
        '''on Close event'''
        self.saveConfig()
        self.Destroy()

#----------------------------------------------------------------
    def initItaly(self):
        '''init of all regions and cities of Italy'''
        self.italy["Abruzzo"]=["L'Aquila","Chieti","Pescara","Teramo"]
        self.italy["Basilicata"]=["Potenza","Matera"]
        self.italy["Calabria"]=["Reggio Calabria","Catanzaro","Crotone","Vibo Valentia Marina","Cosenza"]
        self.italy["Campania"]=["Napoli","Avellino","Caserta","Benevento","Salerno"]
        self.italy["Emilia Romagna"]=["Bologna","Reggio Emilia","Parma","Modena","Ferrara","Forlì Cesena","Piacenza","Ravenna","Rimini"]
        self.italy["Friuli Venezia Giulia"]=["Trieste","Gorizia","Pordenone","Udine"]
        self.italy["Lazio"]=["Roma","Latina","Frosinone","Viterbo","Rieti"]
        self.italy["Liguria"]=["Genova","Imperia","La Spezia","Savona"]
        self.italy["Lombardia"]=["Milano","Bergamo","Brescia","Como","Cremona","Mantova","Monza Brianza","Pavia","Sondrio","Lodi","Lecco","Varese"]
        self.italy["Marche"]=["Ancona","Ascoli Piceno","Fermo","Macerata","Pesaro Urbino"]
        self.italy["Molise"]=["Campobasso","Isernia"]
        self.italy["Piemonte"]=["Torino","Asti","Alessandria","Cuneo","Novara","Vercelli","Verbania","Biella"]
        self.italy["Valle d'Aosta"]=["Aosta"]
        self.italy["Puglia"]=["Bari","Barletta-Andria-Trani","Brindisi","Foggia","Lecce","Taranto"]
        self.italy["Sardegna"]=["Cagliari","Sassari","Nuoro","Oristano","Carbonia Iglesias","Medio Campidano","Olbia Tempio","Ogliastra"]
        self.italy["Sicilia"]=["Palermo","Agrigento","Caltanissetta","Catania","Enna","Messina","Ragusa","Siracusa","Trapani"]
        self.italy["Toscana"]=["Arezzo","Massa Carrara","Firenze","Livorno","Grosseto","Lucca","Pisa","Pistoia","Prato","Siena"]
        self.italy["Trentino Alto Adige"]=["Trento","Bolzano"]
        self.italy["Umbria"]=["Perugia","Terni"]
        self.italy["Veneto"]=["Venezia","Belluno","Padova","Rovigo","Treviso","Verona","Vicenza"]
        for key in self.italy:
            self.italy[key].sort()

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
    def showData(self):
        '''show all data about selected city'''
        start = time.process_time()
        if not is_connected():
            self.result.SetLabel('nessuna connessione di rete presente')
            return
        region = self.cleanName(self.regions.GetString(self.regions.GetSelection()))
        city = self.cleanName(self.cities.GetString(self.cities.GetSelection()))
        try:
            page = requests.get(self.baseUrl + '/coronavirus-italia/coronavirus-' + region + '/coronavirus-' + city +'/')
        except requests.exceptions.RequestException as e:
            self.result.SetLabel('impossibile stabilire la connessione con la fonte\n' + str(e))
            return
        allData = re.findall(r'data:.*', page.text, re.MULTILINE)
        if len(allData) < 4:
            self.result.SetLabel('dati non disponibili per: ' + region + ' ' + city)
            return
        res = allData[3]
        values = [int(x) for x in res[res.find('[') + 1 : res.find(']') - 1].split(',')]
        pyplot.plot(numpy.diff(values))
        pyplot.ylabel('')
        pyplot.xlabel('')
        pyplot.savefig(self.pic)
        pyplot.close()
        with open(self.pic, 'r+b') as file, Image.open(file) as image:
            cover = resizeimage.resize_cover(image, [self.size[0] - 50, 150])
            cover.save(self.respic, image.format)
        self.graph.SetBitmap(wx.Bitmap(self.respic))
        today = datetime.date.today()
        diff = values[-1] - values[-2]
        diff = str(diff) if diff < 0 else '+' + str(diff)
        res =  self.days[today.weekday()] + ' ' + str(today) + '\n'
        res += str(values[-1]) + ' ultimi nuovi positivi ('  + diff + ')\n'
        res += 'statistiche sugli ultimi ' + str(len(values)) + ' giorni' + '\n'
        res += 'media giornaliera: ' + str(round(statistics.mean(values))) + '\n'
        res += 'minimo: ' + str(min(values)) + ', massimo: ' + str(max(values))
        print('retrieved in ' + str(time.process_time() - start) + ' s')
        self.result.SetLabel(res)
        self.panel.SetSize(self.size)
        self.panel.Fit()

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
