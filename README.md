# Indego

## Table of Content

1. [Generell](#generell)
2. [Credits](#credits)
3. [Change Log](#changelog)<sup><span style="color:red"> **Neu**</sup></span>
4. [Konfiguration](#konfiguration)<sup><span style="color:blue"> **Update**</sup></span>
5. [Web-Interface](#webinterface)<sup><span style="color:blue"> **Update**</sup></span>
6. [Logik-Trigger](#logiktrigger)
7. [öffentlich Funktionen (API)](#api)
8. [Gartenkarte "pimpen"](#gardenmap)

## Generell<a name="generell"/></a>

Das Indego-Plugin wurde durch ein Reverse-Engineering der aktuellen (Version 3.0) App
von Bosch entwickelt. Als Basis diente das ursprüngliche Plugin von Marcov. Es werden alle Funktionen der App sowie einige zusätzliche bereitgestellt.
Das Plugin erhält die Version der aktuellen Bosch-API.

## Credits<a name="credits"/></a>

Vielen Dank an schuma für die tolle Unterstützung während der Entwicklungsphase,
die Umsetzung vieler Teile in der Visu sowie den vielen unzähligen Tests und sehr viel Geduld.

Vielen Dank an psilo für die Erlaubnis zur Verwendung der LED-Grafiken im Web-Interface.
Vielen Dank an bmx für das Umstellen des Plugins auf Smart-Plugin.
Vielen Dank an Marcov für die Entwicklung des ursprünglichen Plugins.
Vielen Dank an das Core-Team für die Einführung der STRUCTS, das hat die Arbeit deutlich vereinfacht.
Vielen Dank an Jan Odvarko für die Entwicklung des [Color-Pickers](#http://jscolor.com) unter Freigabe für Opensource mit GPLv3   

## Change Log<a name="changelog"/></a>

#### 2019-10-28 V3.0.0
- Kommunikation auf requests geändert
- Verwendung von vordefinierten STRUCTS für alle benötigten Items
- verbessertes Login/Session-Handling
- Umstellung auf Code64 verschlüsselte Credentials
- Integration eines Wintermodus wenn der Mäher stillgelegt ist
- Integration der Mähkalenderverwaltung
- Integration der SmartMow-Einstellungen
- Integration "Mähen nach UZSU"
- verbesserte Darstellung der Icons für das Wetter
- Gartenkarte als Item in Visu integriert
- "pimpen" der Gartenkarte mit eigenen Vektoren
- Mähspurdarstellung für die IndegoConnect 350/400
- Aktualisierung der Mäherposition beim Mähen alle 7 Sekunden
- Darstellung der Informationen zum genutzten GSM-Netz sowie zum verwendeten Standort
- Updatefunktionen für Firmware integriert
- Integration der Sensorempfindlichkeit
- Integration von unterschiedlichen Bilder für Große/Kleine Mäher
- Alarme / Meldungen werden in einem Popup dargestellt und können gelesen/gelöscht werden.
- VISU um Batterie-Informationen erweitert
- diverse Charts für Batterie, Temperatur, Mäheffizienz, Mäh-/Ladezeiten
- Protokoll für Mäher STATI und Bosch-Kommunikation im Web-Interface
- Unterstützung für base64 codierte Credentials im Web-Interface
- Trigger für Alarme und STATI des Mähers im Web-Interface
- Mäherfarbe für die Darstellung der Kartenkarte im Web-Interface wählbar
 



## Requirements

Das Plugin benötigt keine zusätzlichen requirements

### benötigte Software

* SmartVISU 2.9
* smarthomeNg 1.6 oder höher (es werden vordefinierte STRUCTS verwendet)


### Supported Hardware

* Indego Connect 350/S+350/400/S+400 - Indego Connect 800/1000/1200/1300


## Konfiguration<a name="konfiguration"/></a>

### plugin.yaml

folgende Einträge werden in der "./etc/plugin.yaml" benötigt.

* `class_name`:  fix "Indego"
* `class_path`:  fix "plugins.indego"
* `path_2_weather_pics`: ist der Pfad zu den Bilder des Wetter-Widgets.
(default ="/smartVISU/lib/weather/pics/")
* `img_pfad`:  ist der Pfad unter dem die Gartenkarte gespeichert wird. 
(default = "/tmp/garden.svg")
Die Datei wird nicht für die VISU benötigt. Man kann die Datei als Vorlage
zum "pimpen" der Gartenkarte verwenden
* `indego_credentials`:  sind die Zugangsdaten für den Bosch-Server im Format base64 encoded.
* `parent_item`:  name des übergeordneten items für alle Child-Items
* `cycle`:  Intervall in Sekunden für das Abrufen des Mäher-Status

Die Zugangsdaten können nach dem Start des Plugins im Web-Interface erfasst und gespeichert werden 


```yaml
indego:
    class_name: Indego
    class_path: plugins.indego
    #path_2_weather_pics: /smartVISU/lib/weather/pics/
    #img_pfad: /tmp/garden.svg
    indego_credentials:
    parent_item: indego 
    cycle: '30'
    url: https://api.indego.iot.bosch-si.com/api/v1/
```



### items.yaml

Es wird ledigliche folgender Eintrag für die Items benötigt.
Die restlichen Informationen werden aus der mitgelieferten Struct-Definition gelesen.
Eine entsprechende Config-Datei ist im Ordner "items" des Plugins bereits vorhanden und
muss nur in den Ordner "./smarthome/items" kopiert werden.

```yaml
%YAML 1.1
---

indego:
    struct: indego.child
```

### SmartVisu

Die Inhalte des Ordners "./dropins" müssen in den entsprechenden Ordner der VISU.
In der Regel "/var/www/html/smartVISU2.9/dropins" kopiert werden.

Im Ordner "/pages" des plugins ist eine vorgefertigte Raumseite für die SmartVISU.
Diese muss in den Ordner "/pages/DeinName/" kopiert werden und die Raumnavigation entsprechend ergänzt werden.

<strong>!!! Immer auf die Rechte achten !!!</strong> 

## Web-Interface<a name="webinterface"/></a>
Kurze Erläuterung zum Web-Interface
### erster Tab - Übersicht Indego-Items
![Webif-Tab1](./assets/webif1.jpg)



### zweiter Tab - Originalgartenkarte / Settings
Hier wird die Original-Gartenkarte wie sie von Bosch übertragen wird angezeigt.
Es kann mit dem Colour-Picker die Farbe des Mähers in der Visu angepasst werden.
Die Originalkarte bleibt unverändert. Im ersten Tab wird unter dem Item indego.visu.map_2_show
die modifizierte Karte angzeigt.
Es können auf dieser Seite zusätzlich Vektoren eingefügt werden welche die Gartenkarte erweitern bzw."aufhübschen"
[Sieh auch hier](#gardenmap) 


Es können hier bis zu 4 Trigger für Stati gewählt werden. 999999 - kein Status gewählt.
Immer wenn der Status des Mähers auf den gewählten Status wechselt wird das Trigger-item
"indego.trigger.state_trigger_<strong>X</strong>:" (X = 1-4 ) gesetzt. Die Trigger können in einer Logik
verarbeitet werden. Beispiel siehe bei Logiken.
Es können bis zu 4 Texte für Meldungen erfasst werden. Wenn der Text in der Überschrift oder im Inhalt der
Meldung ist wird der Trigger "indego.trigger.alarm_trigger_<strong>X</strong>:" (X = 1-4 ) beim eintreffen der Meldung gesetzt. 

![Webif-Tab1](./assets/webif2.jpg)



### dritter Tab - State-Protokoll
Hier können die einzelnen Statuswechsel des Mähers eingesehen werden.
Es erfolgt bei jedem Statuswechsel ein Eintrag, das Protokoll ist selbst rotierend und hat 
maximal 500 Einträge

![Webif-Tab1](./assets/webif3.jpg)



### vierter Tab - Kommunikationsprotokoll
Hier können Protokoll-Einträge zu den einzelnen Kommunikationsanfragen mit dem Bosch-Server eingesehen werden.
Es erfolgt bei jedem Statuswechsel ein Eintrag, das Protokoll ist selbst rotierend und hat 
maximal 500 Einträge
![Webif-Tab1](./assets/webif4.jpg)


## Logik-Trigger<a name="logiktrigger"/></a>

Über die Items :

<strong>indego.trigger_state_trigger_1(2)(3)(4)</strong>

und
 
<strong>indego.trigger_alarm_trigger_1(2)(3)(4)</strong>

können Events auf state-Wechsel und Meldungen in Logiken ausgeführt werden.
Die Trigger werden über das Web-Interface definiert. Bei den Alarmen wird ein Teil des
Textes der Alarm-Meldung oder der Überschrift angegeben. Groß- Kleinschreibung spielt keine Rolle
Wenn der Text in der Meldung bzw. der Überschrift enthalten ist wird der Trigger ausgelöst.

Beispiel :

```
#!/usr/bin/env python3
# indego2alexa.py

#sys.path.append('/home/smarthome/.p2/pool/plugins/org.python.pydev.core_6.5.0.201809011628/pysrc')
#import pydevd
#pydevd.settrace("192.168.178.37", port=5678)

text=''
try:
    triggeredItem=trigger['source']
    triggerValue = trigger['value']
    
    # Check the State-Items 
    if triggeredItem == 'indego.trigger.state_trigger_1':
        if triggerValue == True:
            text = 'Achtung der Indego nimmt seine Arbeit auf'
    
    elif triggeredItem == 'indego.trigger.state_trigger_2':
        if triggerValue == True:
            text = 'Der Indego hat seine Arbeit getan Danke Indego'        
            
    elif triggeredItem == 'indego.trigger.state_trigger_3':
        if triggerValue == True:
            text = ''        
            
    elif triggeredItem == 'indego.trigger.state_trigger_4':
        if triggerValue == True:
            text = ''        
    
    # Now the Alarm-Items
    if triggeredItem == 'indego.trigger.alarm_trigger_1':
        if triggerValue == True:
            text = 'Achtung der Indego benötigt Wartung'
    
    elif triggeredItem == 'indego.trigger.alarm_trigger_2':
        if triggerValue == True:
            text = 'Achtung der Indego benötigt neue Messer'        
            
    elif triggeredItem == 'indego.trigger.alarm_trigger_3':
        if triggerValue == True:
            text = ''        
            
    elif triggeredItem == 'indego.trigger.alarm_trigger_4':
        if triggerValue == True:
            text = ''
            
    if text != '':
        sh.alexarc4shng.send_cmd_by_curl('Kueche', 'Text2Speech', text);
except:
    pass
```

## öffentliche Funkionen<a name="api"/></a>

Es gibt eine Funktion die z.B. über Logiken aufgerufen werden kann.
#### indego_send(Payload as String)

Man kann so z.B. den Mäher bei einsetzendem Regen der durch die Wetterstation erkannt wird
zurück in die Ladestation schicken.
Anderes Beispiel wäre beim Verlassen des Hauses den Mäher starten.
```
#!/usr/bin/env python3
# indego_rc.py

sh.indego.send_command('{"state":"mow"}')
#sh.indego.send_command(payload:str= '{"state":"pause"}')
#sh.indego.send_command(payload:str= '{"state":"returnToDock"}')

```


Über die Items :
<table>
  <thead>
    <tr>
      <th style="text-align: left">Links ausgerichtet</th>
      <th style="text-align: center">Mittig ausgerichtet</th>
      <th style="text-align: right">Rechts ausgerichtet</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td style="text-align: left">Inhalt</td>
      <td style="text-align: center">Inhalt</td>
      <td style="text-align: right">Inhalt</td>
    </tr>
    <tr>
      <td style="text-align: left">Inhalt</td>
      <td style="text-align: center">Inhalt</td>
      <td style="text-align: right">Inhalt</td>
    </tr>
  </tbody>
</table>

## Gardenkarte "pimpen"<a name="gardenmap"/></a>

Die Gartenkarte wird vom Bosch-Server heruntergeladen und als Item für die Visu verwendet.
Die Datei wird als Vorlage zum Erweitern unter dem angegebenen Pfad gespeichert ( vgl. ```img_pfad``` im Konfig-Teil).

Man kann die Karte als Vorlage in einem [Online-Tool](#https://editor.method.ac/) als Vorlage laden.
Es werden dann einfach die zusätzlichen Vektoren eingezeichnet oder via "File / Import Image" hinzugeladen.

Man kann die veränderte Karte auch lokal zwischenspeichern.

Am Ende wählt man im Menü die Ansicht "View" den Eintrag "Source". Hier kann man die erweiterten Vektoren
einfach in die Zwischenablage kopieren und im Web-Interface unter Tab-2 einfügen.
Der letzte Original-Eintrag der Bosch-Karte ist die Zeile mit
 
```<circle id="svg_8" r="15" cy="792" cx="768" fill="#FFF601" stroke-width="0.5" stroke="#888888"/>```

<strong>Die Werte können abweichen, da hier auch die Position des Mähers sowie die ID enthalten ist. Am besten auf "circle" und den Farbwert "#FFF601" achten.</strong>

Diese Zeile ist der gelbe Punkt (Mäher) in der Originalkarte.
Beim Verlassen der Textarea werden die neuen Vektoren sofort in ein Item gespeichert und die Gartenkarte neu gerendert.
Das Ergebnis ist in der VISU sofort sichtbar.

## Beispiel :

![pimp_my_map](./assets/pimp_my_map.jpg)
