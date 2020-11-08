import wx
import re
import requests
import datetime
import statistics

class CowWnd(wx.Frame): 
    def __init__(self, parent, title): 
        super(CowWnd, self).__init__(parent, title = title,size = (250,250), style = wx.DEFAULT_FRAME_STYLE & ~(wx.RESIZE_BORDER | wx.MAXIMIZE_BOX))
        self.italy = {}
        self.initItaly()
        self.baseUrl = 'https://statistichecoronavirus.it'
        self.days = ["Lunedì","Martedì","Mercoledì","Giovedì","Venerdì","Sabato","Domenica"]

        self.panel = wx.Panel(self) 
        box = wx.GridBagSizer()

        regions = list(self.italy.keys())

        static = wx.StaticText(self.panel, label = "Regione", style = wx.LEFT) 
        box.Add(static, pos = (0, 0), flag = wx.EXPAND|wx.ALL, border = 5)
        self.regions = wx.Choice(self.panel, choices = regions)
        box.Add(self.regions, pos = (0, 1), flag = wx.EXPAND|wx.ALL, border = 5) 

        static = wx.StaticText(self.panel, label = "Provincia", style = wx.ALIGN_LEFT)   
        box.Add(static, pos = (1, 0), flag = wx.EXPAND|wx.ALL, border = 5) 
        self.cities = wx.Choice(self.panel, choices = list(self.italy[regions[0]]))
        box.Add(self.cities, pos = (1, 1), flag = wx.EXPAND|wx.ALL, border = 5)

        self.result = wx.StaticText(self.panel, style = wx.ALIGN_CENTER) 
        box.Add(self.result, pos = (2, 0), flag = wx.EXPAND|wx.ALL, border = 5, span = (1, 2))
        self.updateRes()

        self.regions.Bind(wx.EVT_CHOICE, self.OnRegions) 
        self.cities.Bind(wx.EVT_CHOICE, self.OnCities)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.panel.SetSizerAndFit(box) 
        self.Centre() 
        self.Show() 

    def onClose(self, event):
        self.Destroy()

    def initItaly(self):
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

    def OnRegions(self, event):
        self.cities.SetItems(self.italy[self.regions.GetString(self.regions.GetSelection())])
        self.updateRes()

    def updateRes(self):
        region = self.cleanName(self.regions.GetString(self.regions.GetSelection()))
        city = self.cleanName(self.cities.GetString(self.cities.GetSelection()))
        
        page = requests.get(self.baseUrl + '/coronavirus-italia/coronavirus-' + region + '/coronavirus-' + city +'/')
        allData = re.findall(r'data:.*', page.text, re.MULTILINE)
        if len(allData) < 4:
            res = 'dati non disponibili per: ' + region + ' ' + city
        else:
            res = allData[3]
            values = [int(x) for x in res[res.find('[') + 1 : res.find(']') - 1].split(',')]
            today = datetime.date.today()
            diff = str(values[-1] - values[-2]) if values[-1] - values[-2] < 0 else '+' + str(values[-1] - values[-2])
            res =  self.days[today.weekday()] + ' ' + str(today) + '\n'
            res += str(values[-1]) + ' ultimi nuovi positivi ('  + diff + ')\n'
            res += 'statistiche sugli ultimi ' + str(len(values)) + ' giorni' + '\n'
            res += 'media giornaliera: ' + str(round(statistics.mean(values))) + '\n'
            res += 'minimo: ' + str(min(values)) + ', massimo: ' + str(max(values)) + '\n\n'
            res += 'fonte: ' + self.baseUrl + '\n'
        self.result.SetLabel(res)

    def OnCities(self, event):
        self.updateRes()

    def cleanName(self, name):
        return name.lower().replace(' ', '-').replace('\'', '-')

if __name__ == "__main__":              
    app = wx.App() 
    CowWnd(None, 'Covid19 Report') 
    app.MainLoop()
