# **Systemarchitektur und Datenquellen für die Kartierung essbarer Biodiversität im Food Atlas**

Die Konstruktion eines rückverfolgbaren Lexikons der essbaren Biodiversität erfordert die Überwindung einer fundamentalen Diskrepanz: Während Standardnährwerttabellen Lebensmittel auf ein knappes Dutzend makronutritiver Durchschnittswerte aggregieren und dabei genetische Varianzen einebnen, umfasst die tatsächliche chemische Komplexität unserer Nahrung zehntausende distinkte Verbindungen1. Wie die Leitstudie von Gupta et al. (2026) anhand von 322 standardisiert analysierten Nahrungsmitteln demonstriert, verteilen sich 27.713 detektierte molekulare Merkmale so spezifisch, dass 44 % davon in lediglich einem einzigen Lebensmittel nachweisbar sind1. Konventionelle kulinarische Bezeichnungen versagen bei der biochemischen Abbildung: Weißer Reis clustert metabolomisch im Raum industriell hochverarbeiteter Produkte, während Xanthan molekular mit Walnüssen gruppiert1. Kein existierendes Monolithsystem verknüpft botanische Taxa, infraspezifische Sorten, anatomische Pflanzenteile und Verarbeitungsstufen durchgängig mit laboranalytischen Primärdaten und molekularer Bioaktivität1.

Für das Produkt Food Atlas ist daher eine föderierte Datenarchitektur unverzichtbar, die drei spezialisierte Datenkorpora über eine formale semantische Ontologie zusammenführt. Das taxonomische Fundament bilden die *World Checklist of Useful Plant Species* der Royal Botanic Gardens, Kew (7.039 validierte Nahrungspflanzen)3, *Mansfeld’s World Database of Agricultural and Horticultural Crops* (über 6.100 Kulturpflanzenarten mit tiefer Gliederung in Varietäten und Konvarietäten)5 sowie USDA *GRIN-Global World Economic Plants*8. Die nutritive Primärebene (Tier 1\) stützt sich auf die *FAO/INFOODS Food Composition Database for Biodiversity* (BioFoodComp 4.0; 10.156 disaggregierte, rein analytische Profile)10, flankiert von den laborauditierten Einzelmessungen der *USDA FoodData Central Foundation Foods*12 und dem britischen *CoFID*\-Korpus14. Die Erschließung der metabolomischen Dunklen Materie erfolgt über *FooDB* (\>26.000 bis \>70.000 chemische Entitäten)16, die chromatographisch kuratierte Polyphenoldatenbank *Phenol-Explorer 3.6*19 und die hochauflösenden Multi-Omics-Profile der *Periodic Table of Food Initiative* (PTFI; Jarvis et al. 2024\)21.

Die operative Integration dieser heterogenen Quellen wird durch die OBO-Foundry-Ontologie *FoodOn* gesteuert23. Die Durchsetzung des Traceability Contracts garantiert, dass jeder Wert als atomares Anspruchsobjekt fungiert, das zwingend Messmethode, physikalische Bezugsbasis (Frischgewicht versus Trockenmasse) und das spezifische Pflanzenorgan deklariert1. Unvollständige oder unvalidierte Datensätze werden isoliert und in ein systematisches Register offener Forschungsfragen überführt1.

## **Taxonomische Grundlagen und infraspezifische Nomenklaturregister**

Eine Hauptursache für Dateninkonsistenzen in lebensmittelchemischen Repositorien liegt in der unpräzisen biologischen Benennung. Trivialnamen sind regional polysem, und viele Datenbanken führen Zuchtformen, morphologische Pflanzenteile oder gar Verarbeitungszustände fälschlich als eigene Arten1. Für das Register *Organismen* im Food Atlas ist eine strikte Trennung zwischen biologischem Quellorganismus, landwirtschaftlicher Kultivarsippe und der konsumierten morphologischen Entität erforderlich1.

### **Mansfeld’s World Database of Agricultural and Horticultural Crops**

Die am Leibniz-Institut für Pflanzengenetik und Kulturpflanzenforschung (IPK) Gatersleben entwickelte und von Peter Hanelt herausgegebene Enzyklopädie stellt das methodisch tiefste Referenzwerk für Kulturpflanzen dar5. Mit einem Gesamtumfang von 3.645 Seiten in sechs Bänden und über 6.100 erfassten Kulturpflanzenarten liefert Mansfeld die im Agrarbereich notwendige infraspezifische Klassifikation5.

Mansfeld führt systematische Rangstufen unterhalb der Speziesebene ein: Unterart (*subspecies*), Konvarietät (*convarietas*) und Varietät (*varietas*)7. Am Beispiel von *Brassica oleracea* L. wird der Wert dieser Struktur deutlich: Anstatt Weißkohl, Blumenkohl, Brokkoli, Kohlrabi und Rosenkohl als undifferenzierte Pflanze zu führen, erlaubt Mansfeld die präzise Zuordnung zu *B. oleracea* convar. *capitata*, convar. *botrytis*, convar. *italica*, convar. *gongylodes* bzw. convar. *gemmifera*7. Neben vollständigen Synonymiebäumen und botanischen Autorenschaften dokumentiert das Werk Domestikationszentren, Wildstammformen, historische Anbaugebiete und primäre Nutzungszwecke5. Der Datenbestand ist am IPK digital erschlossen und dient als primärer Referenzstandard für Domestikationslinien6.

### **Kew World Checklist of Useful Plant Species**

Die von den Royal Botanic Gardens, Kew, im Jahr 2020 veröffentlichte *World Checklist of Useful Plant Species* (WCUPS; Diazgranados et al., DOI:10.5063/F1CV4G34) bildet das umfassendste bereinigte Nomenklaturverzeichnis für ökonomisch genutzte Gefäßpflanzen3. Aus einem Gesamtkorpus von 40.291 nützlichen Pflanzenarten filtert der Datensatz exakt 7.039 Taxa heraus, die verifiziert der menschlichen Ernährung dienen (*Human Food*)3.

Der entscheidende Vorteil von WCUPS liegt in der vollständigen Abstimmung mit den taxonomischen Backbones von *Plants of the World Online* (POWO) und dem *International Plant Names Index* (IPNI)28. Historische botanische Homonyme und heterotypische Synonyme wurden durch das Kew-Team bereinigt4. Der Datensatz liegt als maschinenlesbare Tabelle mit Zuordnung zu standardisierten Nutzungsklassen nach TDWG-Level vor und fungiert im Food Atlas als initialer Validierungsfilter auf Artebene4.

### **USDA GRIN-Global World Economic Plants**

Das Repositorium *World Economic Plants: A Standard Reference* (WEP), kuratiert von John H. Wiersema und Blanca León im Rahmen des Germplasm Resources Information Network (GRIN-Global), dokumentiert über 12.000 wirtschaftlich bedeutsame Pflanzentaxa8.

WEP verknüpft Nomenklaturdaten mit geografischen Ursprungsräumen nach dem TDWG-Standard für weltweite Florengebiete, ökonomischen Verwendungsdaten und dem internationalen Regulierungsstatus8. Die Stärke des WEP-Systems liegt in seiner Kopplung an die aktiven Genbank-Akzessionen des National Plant Germplasm System (NPGS)34. Hierüber können phänotypische Beschreibungen direkt mit konkreten Keimplasma-Beständen verbunden werden, was für die Ausgestaltung des Varietäten-Registers unverzichtbar ist1.

### **Kompendien wilder, traditioneller und ungenutzter Nahrungspflanzen**

Ergänzend zu den agrarisch etablierten Kulturarten existieren spezialisierte Kompendien, die für das Biodiversitäts-Funnel des Food Atlas herangezogen werden müssen, um vormals unsichtbare Arten systematisch zu erfassen1:

* *Cornucopia II: A Source Book of Edible Plants* von Stephen Facciola (Kampong Publications 1998, 713 Seiten): Dieses Standardwerk beschreibt über 3.000 essbare Pflanzenarten detailliert mit tausenden spezifischen Kultivaren36. Facciolas wesentliche Leistung besteht in der genauen Nennung des jeweils essbaren anatomischen Organs (z. B. Rhizome, Blattstiele, Blütenknospen, Samen, Exsudate) sowie der spezifischen kulinarischen Verwendungsform (z. B. gekocht, milchsauer vergoren, gemahlen)36.  
* *Plants For A Future* (PFAF): Eine strukturierte Datenbank mit über 7.000 Nutz- und Nahrungspflanzen für gemischte und kältere Klimazonen40. PFAF implementiert ein empirisches Bewertungsraster: Jede Pflanze erhält diskrete Ratings für Genießbarkeit (*Edible Rating*, 1–5), medizinische Verwendung (*Medicinal Rating*, 0–5) sowie explizit dokumentierte Giftstoffe (*Known Hazards*)42. Die Gesamtdatenbank steht im CSV- und SQL-Format für relationale Ingestionen bereit40.  
* *PROTA* (Plant Resources of Tropical Africa) und *PROSEA* (Plant Resources of South-East Asia): Diese über die Pl@ntUse-Plattform konsolidierten Monographienwerke beschreiben tausende indigene afrikanische und südostasiatische Nutzpflanzenarten46. Sie liefern agronomische Ertragsdaten, traditionelle Verarbeitungsschritte und phytochemische Beschreibungen für vernachlässigte Wildgemüse, Knollen und Waldobstarten47.

&nbsp;

| Enzyklopädie / Register | Träger / Autorenschaft | Taxonomischer Umfang | Infraspezifische Auflösung | Funktionale Rolle im Food Atlas | Bereitstellungsformat |
| :---- | :---- | :---- | :---- | :---- | :---- |
| **Mansfeld’s Database** | IPK Gatersleben / Hanelt et al.5 | \~6.100 Kulturpflanzenarten5 | Subspecies, Convarietäten, Varietäten, Landsorten7 | Taxonomisches Rückgrat für Kulturvarietäten und Domestikation1 | Web-Interface, IPK-Archivauszüge6 |
| **Kew WCUPS 2020** | RBG Kew / Diazgranados et al.3 | 40.291 Nutzpflanzen (7.039 Nahrungspflanzen)3 | Rein Artebene (strikt nach POWO/IPNI)28 | Globaler Validierungsfilter für essbare Arten4 | CSV, KNB/Darwin Core Archive3 |
| **USDA WEP / GRIN** | USDA ARS / Wiersema & León8 | \>12.000 ökonomische Pflanzentaxa9 | Arten, Varietäten, Subspecies, NPGS-Akzessionen34 | Verknüpfung von Taxa mit Keimplasma und Geodaten1 | Relationale SQL-Dumps, REST-API50 |
| **Cornucopia II** | Kampong Publ. / Stephen Facciola37 | \>3.000 essbare Arten, tausende Kultivare36 | Extrem hoch (Handelssorten, Landsorten)36 | Referenz für essbare Pflanzenteile und Zubereitungen1 | Monographie (Print/Digital; OCR-Kuration)38 |
| **Plants For A Future** | PFAF Charity Association40 | \>7.000 Nutzpflanzenarten41 | Sorten, Ökotypen, spezifische Pflanzenorgane43 | Kuration von Genießbarkeit, Toxizität und Standort1 | Relationale SQL- und CSV-Dateien40 |
| **PROTA / PROSEA** | Wageningen Univ. / Pl@ntUse46 | \>9.000 tropische Nutzpflanzen47 | Sorten, Landsorten, Wildtypen46 | Regionaldaten für vernachlässigte tropische Nutzpflanzen47 | MediaWiki Dump, Semantic MediaWiki API46 |

## **Primäranalytische Nährstoffdatenbanken mit Sorten- und Gewebedifferenzierung**

Klassische Nährwerttabellen bilden Mischproben des Lebensmitteleinzelhandels ab1. Die tatsächliche Nährstoffdichte schwankt jedoch sorten- und herkunftsbedingt dramatisch: So variiert der Gehalt an Provitamin A in Süßkartoffeln (*Ipomoea batatas*) zwischen weißfleischigen Lokalsorten und orangefleischigen Neuzüchtungen um mehr als den Faktor 10010. Für ein evidenzbasiertes Produktsystem dürfen daher nur Datenquellen herangezogen werden, die ausschließlich analytische Messwerte mit dokumentierter Methodik vorweisen1.

### **FAO/INFOODS Food Composition Database for Biodiversity**

Die von der FAO und dem International Network of Food Data Systems herausgegebene *Food Composition Database for Biodiversity* (BioFoodComp Version 4.0, 2017, ISBN 978-92-5-109790-8) ist die weltweit führende Sammlung rein analytischer Nährwertdaten auf infraspezifischer Ebene10. Das Korpus umfasst 10.156 disaggregierte Lebensmitteleinträge10:

* Hülsenfrüchte (Legumes): 2.151 Einträge10  
* Wurzeln und stärkehaltige Knollen: 1.985 Einträge (davon 1.671 distinkte Kartoffelsorten)10  
* Früchte: 1.704 Einträge (disaggregiert nach Varietäten und Reifestadien)10  
* Fisch und Meeresfrüchte: 1.542 Einträge10  
* Fleisch und Geflügel: 1.265 Einträge (einschließlich 471 quantifizierter Speiseinsekten)10  
* Getreide: 709 Einträge10  
* Gemüse: 419 Einträge10  
* Milch diverser Tierarten: 273 Einträge (differenziert nach Ziege, Schaf, Büffel, Yak, Kamel, Pferd, Rentier)10

BioFoodComp 4.0 folgt drei methodischen Leitlinien, die den Kern von Tier 1 im Traceability Contract verkörpern1:

> 1. *Ausschluss imputierter Werte:* Das Kompendium enthält ausnahmslos gemessene Daten aus Primärliteratur, Berichten und Laboranalysen; es existieren keine geschätzten oder errechneten Lückenfüller10.  
> 2. *Standardisierung auf Frischgewicht (EP FW):* Sämtliche Konzentrationen sind normiert auf 100 g verzehrbaren Anteil auf Frischmassebasis (*edible portion on a fresh weight basis*)10. Primärdaten, die ausschließlich auf Trockenmasse bezogen waren und keine verlässliche Rückrechnung des Wassergehalts erlaubten, wurden eliminiert10. Dies schützt das System vor Fehlern, wie sie beim automatisierten Scraping auftreten (wo getrocknete Proben fälschlich als Frischware interpretiert werden)1.  
> 3. *Strikte INFOODS-Tagnames:* Zur chemischen Eindeutigkeit werden standardisierte Tagnames genutzt, etwa bei der Differenzierung von Phytatfraktionen (IP6, IP5, PHYTCPPI) anstelle unpräziser Sammelbezeichnungen10.

Ergänzend liefert die *FAO/INFOODS Food Composition Table for Western Africa* (WAFCT 2019\) 1.028 profilierte Nahrungsmittel mit 47 Nährstoffen49. Sie enthält analytische Werte für untergenutzte afrikanische Arten wie Bambara-Erdnuss (*Vigna subterranea*), Fonio-Hirse (*Digitaria exilis*) oder Baobab-Fruchtfleisch (*Adansonia digitata*)49.

### **USDA FoodData Central Foundation Foods**

Innerhalb des USDA FoodData Central (FDC) Ökosystems stellt die *Foundation Foods*\-Kategorie den methodischen Paradigmenwechsel dar12. Während frühere Tabellenwerke (SR Legacy) statische Mittelwerte publizierten, erfasst Foundation Foods die zugrundeliegenden chemischen Einzelanalysen (*analytical sample results*) zusammen mit umfangreichen landwirtschaftlichen Metadaten: Kultivar, Anbauort, Bodenparameter, Düngungspraxis, Erntezeitpunkt und Reifegrad12.

Die Nährstoffwerte werden durch validierte chemische Analyseverfahren gewonnen (z. B. Atomemissionsspektrometrie mit induktiv gekoppeltem Plasma \[ICP-AES/MS\] für Mineralstoffe, Ultrahochleistungs-Flüssigchromatographie mit Tandem-Massenspektrometrie \[UHPLC-MS/MS\] für Vitamine)12. Die Daten werden über eine offene REST-API und relationale Downloads im JSON- und CSV-Format bereitgestellt12.

### **McCance and Widdowson’s Composition of Foods Integrated Dataset**

Das vom britischen Quadram Institute herausgegebene Referenzwerk *McCance and Widdowson’s The Composition of Foods* (aktuell gepflegt als *Composition of Foods Integrated Dataset*, CoFID) stellt den europäischen Goldstandard dar14. CoFID besticht durch eine lückenlose Erfassung komplexer Nährstofffraktionen, darunter detaillierte Fettsäurespektren (gesättigte, cis-/trans-ungesättigte Isomere), Aminosäureprofile sowie die Differenzierung von Stärke, Freizuckern und nicht-stärkehaltigen Polysacchariden (Englyst- versus AOAC-Ballaststofffraktionierung)14. Die Daten liegen als relationale Tabellen vor und decken rund 3.000 Grundnahrungsmittel und Zubereitungen ab14.

### **CINE Traditional Food Systems of Indigenous Peoples**

Das am Centre for Indigenous Peoples' Nutrition and Environment (CINE) der McGill University in Zusammenarbeit mit der FAO entwickelte Korpus umfasst Nährstoffanalysen von über 3.000 traditionellen Nahrungsmitteln indigener Völker58. Es dokumentiert quantitative Laboranalysen für arktische Meeressäuger, Wildfische, Wüstenleguminosen und Wildbeeren Nordamerikas, des Amazonasgebiets sowie mikronährstoffreicher Pflanzen ländlicher Gemeinschaften Indiens60. Die CINE-Monographien bilden ein Gegengewicht zur eurozentrischen Ausrichtung westlicher Nährstofftabellen59.

## **Chemoinformatik und die molekulare Dunkle Materie der Ernährung**

Die klassische Ernährungswissenschaft operiert historisch mit einem reduzierten Katalog von 20 bis 150 Nährstoffen1. Dies blendet die Gesamtheit sekundärer Pflanzenstoffe, Peptide, Terpenoide und Polyphenole aus, die für die physiologische Wirkung im menschlichen Körper mitverantwortlich sind2. Barabási, Menichetti und Loscalzo definieren diese unkartierte Diversität als die "Dunkle Materie" der Ernährung (*nutritional dark matter*)2.

### **FooDB: Umfassender chemischer Referenzgraph**

FooDB (foodb.ca, entwickelt am The Metabolomics Innovation Centre, TMIC) ist die weltweit größte offene Datenbank für Lebensmittelinhaltsstoffe17. Sie aggregiert strukturierte Daten zu über 26.000 diskreten chemischen Verbindungen (in Rohversionen über 70.000 inklusive Stellungsisomeren) über hunderte Lebensmittelentitäten16.

Jedes Molekül ist mit strukturellen Identifikatoren annotiert: ChEBI-IDs, PubChem-CIDs, InChIKeys, SMILES, Molekulargewichten und berechneten physikochemischen Deskriptoren16. FooDB enthält darüber hinaus ein Vokabular olfaktorischer und gustatorischer Aromaprofile für tausende Verbindungen68.

Für den Traceability Contract des Food Atlas weist FooDB jedoch zwei strukturelle Risiken auf1:

> 1. *Mangelnde quantitative Konsistenz:* Während hunderttausende Verknüpfungen lediglich das qualitative Vorkommen anzeigen (*contains*), verfügen nur wenige Datensätze über verifizierte Konzentrationswerte1.  
> 2. *Fehlende Bezugsbasis:* Historische Literaturdaten enthalten Konzentrationswerte, bei denen Frisch- und Trockengewichtsbasen vermengt wurden1.

In der Ingestionspipeline des Food Atlas müssen FooDB-Einträge daher aufgespalten werden: Verifizierte Messwerte wandern in Tier 1 oder Tier 3, unvollständig dokumentierte Werte werden als qualitative Anwesenheitsnachweise geführt1. Der FooDB-Datenbestand steht im CSV-, SQL- und JSON-Format uneingeschränkt zur Verfügung16.

### **Phenol-Explorer 3.6**

Phenol-Explorer (INRAE, Universität Barcelona, University of Alberta) ist die internationale Referenz für Polyphenolgehalte in Nahrungsmitteln19. Das Repositorium umfasst über 37.000 manuell kuratierte quantitative Gehaltseinträge für mehr als 500 Polyphenolverbindungen in über 500 Lebensmitteln19.

Der entscheidende architektonische Vorzug von Phenol-Explorer ist die methodische Disaggregation71:

* HPLC ohne Hydrolyse (Messung nativer Glykoside und Ester)71  
* HPLC nach chemischer oder enzymatischer Hydrolyse (Messung von Gesamt-Aglyka)71  
* Spektrophotometrische Summenparameter (Folin-Ciocalteu-Assays)72

Zusätzlich erfasst Phenol-Explorer in Version 3.0ff. quantitative Retentionsfaktoren für Lebensmittelzubereitungen74. Damit lässt sich rechnerisch nachverfolgen, wie Garverfahren (Kochen, Braten, Dämpfen, Mikrowellenerhitzen) oder Lagerzeiten das Polyphenolprofil verändern74. Dies macht Phenol-Explorer zu einer Tier-1-Quelle für das Prozess-Register des Food Atlas1.

### **Periodic Table of Food Initiative und empirische Multi-Omics**

Die *Periodic Table of Food Initiative* (PTFI, Jarvis et al. 2024, *Nature Food*) verfolgt das Ziel, die biomolekulare Zusammensetzung von rund 1.600 prioritären Nahrungsmitteln weltweit hochauflösend zu kartieren21. Das Konsortium fokussiert gezielt auf die Erfassung traditioneller, vernachlässigter und klimaresistenter Arten21.

Die methodische Basis bilden standardisierte Hochdurchsatz-Plattformen: hochauflösende Massenspektrometrie (HRMS), nicht-zielgerichtete Metabolomik (*untargeted metabolomics*), Ionomik, Glykomik und Lipidomik21. Die Pionierstudie von Gupta et al. (2026, *npj Science of Food*) quantifiziert 27.713 molekulare Merkmale über 322 Lebensmittel und ordnet diese mittels Algorithmen 11 therapeutischen Evidenzkategorien zu1.

&nbsp;

| Chemische / Multi-Omics-Datenbank | Träger / Konsortium | Profilierte Molekülklassen | Datenumfang & Entitäten | Quantifizierungsgrad & Methodik | Rolle im Traceability Contract | Datenlizenz & Zugriff |
| :---- | :---- | :---- | :---- | :---- | :---- | :---- |
| **FooDB** | The Metabolomics Innovation Centre17 | Nährstoffe, Sekundärmetabolite, Aromastoffe17 | \>26.000 bis \>70.000 Verbindungen; \>1.000 Lebensmittel16 | Gemischt: Hohe qualitative Dichte; quantitative Werte teils ohne Basis1 | Tier 1 (bei voller Provenienz) bis Tier 31 | Open Access (CSV, XML, JSON, SQL)16 |
| **Phenol-Explorer 3.6** | INRAE / Univ. Barcelona / TMIC19 | Ausschließlich Polyphenole (Flavonoide, Lignane, Stilbene)19 | \>37.000 Gehaltswerte; 500 Polyphenole in 500 Lebensmitteln19 | Sehr hoch: 100 % manuell kuratierte HPLC-Messungen20 | Tier 1 (chromatographischer Goldstandard)1 | Open Access (Tabellarische Downloads)19 |
| **PTFI Metabolomics** | Bioversity / Rockefeller / AHA1 | Vollständige Multi-Omics, Lipidomik, Dunkle Materie1 | 1.600 Nahrungsmittel; 27.713 Features über 322 Kernspezies1 | Höchste analytische Einheitlichkeit (HRMS/MS)1 | Tier 1 (Analysen) / Tier 4 (Bioaktivitäts-Scores)1 | CC BY-NC 4.0 (AHA PMP Plattform)1 |
| **FoodAtlas v4.11** | Tagkopoulos Lab / UC Davis1 | Wissensgraph: Nahrung – Chemie – Krankheit – Phänotyp1 | 10.270 Lebensmittel; 193.236 Chemikalien; 542.953 Kanten1 | Sehr gering: Nur 2,4 % der Kanten tragen Mengenangaben1 | Tier 3 (markiert als llm\_extracted / unvalidated)1 | Apache-2.0 Bundle (Parquet-Dateien)1 |

## **Semantische Wissensgraphen und ontologische Normalisierung**

Die strukturelle Evaluation von FoodAtlas v4.11 zeigt die Gefahren unkontrollierter Wissensextraktion1:

* Nur 2,4 % der Kanten (15.726 Zeilen) enthalten quantitative Konzentrationswerte1.  
* Die Felder für Pflanzenteil (food\_part) und Verarbeitung (food\_processing) sind in über 99,99 % der Zeilen unbesetzt1.  
* Infraspezifische Ebenen sind vermengt: Die Art *Malus domestica* führt 15 Kind-Entitäten, darunter 13 Handelssorten (z. B. 'Honeycrisp', 'Fuji'), die wilde Stammart *Malus sieversii* sowie den Zustand "Apfel (roh)" auf derselben Ebene1.  
* Trockenmassewerte wurden ohne Basiskennzeichnung importiert, wodurch ein Apfel fälschlich mit 94 g Kohlenhydraten pro 100 g Frischgewicht ausgewiesen wird1.  
* Chemikalien sind redundant: L-Ascorbinsäure, L-Ascorbat und Vitamin C treten als parallele Entitäten auf1.

Zur Behebung dieser Mängel muss der Wissensgraph des Food Atlas auf standardisierte OBO-Foundry-Ontologien umgestellt werden1.

### **FoodOn als hierarchischer Integrationsstandard**

*FoodOn* überführt das klassische LanguaL-Klassifikationssystem in eine formale OWL-Repräsentation mit über 30.000 Konzepten23. FoodOn löst die semantische Modellierung über drei primäre OBO-Relationen24:

* derives from (RO\_0001000): Verknüpft das verzehrte Produkt mit dem Quellorganismus80. Ein Apfelsaft leitet sich ontologisch von *Malus domestica* ab1.  
* has part (BFO\_0000051): Modelliert die anatomische Untergliederung82. Die Entität "Apfel, ganz" besitzt morphologische Teile wie Fruchtschale (*exocarp*), Fruchtfleisch (*mesocarp*) und Kerne (*seeds*)1. Damit erhält jeder Nährstoff- und Molekülwert eine unverrückbare anatomische Verankerung1.  
* Prozesskanten: Über PO2 (Process and Observation Ontology) modelliert FoodOn technologische Transformationen wie Mahlen, Fermentieren, Pressen und Trocknen1.

### **Chemoinformatische Deduplizierung und taxonomische Verankerung**

Zur Eliminierung molekularer Redundanzen werden alle chemischen Entitäten des *Molecules*\-Registers über standardisierte InChIKeys gehasht und auf Primärregister gemappt1:

* *ChEBI* (Chemical Entities of Biological Interest): Liefert die strukturierte chemische Ontologie, funktionale Gruppen und biologische Rollen1.  
* *PubChem*: Stellt CIDs und Assay-Referenzen für Tier-3-Literaturabgleiche bereit1.  
* *CDNO* (Nutritional Component Ontology): Definiert physiologische Nährstoffkonzepte und verhindert Begriffsverwirrungen zwischen chemischen Reinsubstanzen und Nährwertäquivalenten (z. B. Alpha-Tocopherol versus Vitamin-E-Äquivalente)1.  
* *NCBI Taxonomy* und *GBIF Backbone*: Jedes Lebensmittel im *Foods*\-Register wird an eine valide NCBI-Taxon-ID gekoppelt1. Dadurch werden geografische Vorkommensdaten (GBIF) und globale Produktionsmengen (FAOSTAT) automatisiert aggregierbar1.

## **Validierungsregeln und relationale Datenpipeline des Traceability Contracts**

Um die wissenschaftliche Integrität des Food Atlas sicherzustellen, wird jeder Datenpunkt vor der Publikation durch ein strenges Validierungsgitter geschleust1. Die acht Regeln des Traceability Contracts definieren dabei unverhandelbare Invarianten für das Datenmodell1:

> 1. *Regel 1 & 2 (Anspruchsobjekt und Provenienz):* Jeder Wert wird als immutable Claim-Objekt geführt: {v, unit, basis, food\_part, src, tier, method}1. Jeder Quellverweis src muss in ein registriertes Quellendokument mit persistentem Bezeichner (DOI, ISBN, Genbank-ID) auflösen1.  
> 2. *Regel 3 & 4 (Geltungsbereich und Link-Integrität):* Eine Quelle kann nur Claim-Gruppen stützen, für die sie qualifiziert ist1. Ernährungsdaten dürfen keine phänologischen Saisonangaben stützen; tote Links führen zur automatischen Quarantäne1.  
> 3. *Regel 6 (Deklarationspflicht für Basis und Organ):* Ein Gehaltswert wird nur publiziert, wenn seine physikalische Basis explizit deklariert ist: Frischgewicht (*fresh weight*, FW), Trockenmasse (*dry weight*, DW) oder Verkaufsform (*as sold*)1. Zudem muss das Organ (food\_part) exakt benannt sein1. Werte ohne Basis- oder Organbezug werden blockiert und in das *Gaps-Register* verschoben1.  
> 4. *Regel 7 (Strikte Modelltrennung):* Maschinell vorhergesagte Molekülstrukturen oder berechnete Bioaktivitäts-Scores (z. B. nach Gupta et al. 2026\) dürfen niemals als analytische Messwerte dargestellt werden; sie müssen Modellname, Modellversion und die Einstufung in Tier 4 tragen1.  
> 5. *Regel 8 (Bioaktivität als Evidenz):* Das System schließt verallgemeinernde gesundheitsbezogene Aussagen im Sinne der Verordnung (EG) 1924/2006 aus1. Anstelle von Formulierungen wie *"antientzündliches Lebensmittel"* deklariert der Atlas neutral: *"Verbindungsspezifische In-vitro-Assay-Evidenz für anti-inflammatorische Signalwege"*1.

&nbsp;

| Pipeline-Phase | Primäre Datenquellen | Angewandte Transformationen & Normalisierungen | Angewandte Validierungsregeln | Zustand im Zielregister |
| :---- | :---- | :---- | :---- | :---- |
| **Phase 1: Taxonomischer Basis-Build** | Kew WCUPS 2020, Mansfeld, USDA WEP, NCBI Taxonomy1 | Namensbereinigung gegen POWO/IPNI; Auflösung botanischer Synonyme; Aufbau der Artbäume4 | **Tier 2-Prüfung:** Nur valide botanische Binome; Trennung von Wildarten und Hybriden1 | *Organisms-Register:* Konsistente Speziesbäume mit Vorkommensdaten1 |
| **Phase 2: Infraspezifische Strukturierung** | Mansfeld, USDA GRIN, BioFoodComp 4.0, FoodOn7 | Zuordnung zu den vier typisierten Ebenen: Species Food, Cultivar/Variety, Part, Form1 | **Regel 1 & FoodOn:** Auflösung zyklischer oder unpräziser *is\_a*\-Beziehungen via derives from \[cite: 1, 80\] | *Foods-Register:* Eindeutig typisierte Hierarchien von der Sorte bis zur Zubereitung1 |
| **Phase 3: Ingestion analytischer Nährwerte** | BioFoodComp 4.0, USDA Foundation Foods, UK CoFID, CINE10 | Einlesen von Einzelsubstanzen; Umrechnung auf standardisierte 100-g-Einheiten10 | **Regel 6:** Zwingender Nachweis von basis (EP FW) und food\_part; Ausschluss von Mischdaten1 | *Nutrition-Layer:* Rein analytische Nährstoffprofile auf Tier-1-Niveau1 |
| **Phase 4: Molekulare & Polyphenol-Kuration** | Phenol-Explorer 3.6, FooDB, ChEBI, CDNO1 | InChIKey-Hashing; Deduplizierung chemischer Trivialnamen; Extraktion von Retentionsfaktoren1 | **Regel 1 & 6:** Trennung quantitativer HPLC-Werte (Tier 1\) von qualitativen Kanten (Tier 3\)1 | *Molecules-Register:* Deduplizierte Sekundärmetabolite samt Aromadeskriptoren1 |
| **Phase 5: Multi-Omics & Bioaktivitäts-Mapping** | PTFI Core, Gupta et al. (2026), FRAP-Assay-Daten1 | Einbindung hochauflösender Massenspektrometrie-Features; Projektion in Ähnlichkeitsräume1 | **Regel 7 & 8:** Deklaration als Modelloutput (Tier 4); strikter Ausschluss von Health Claims1 | *Bioactivity-Layer:* Molekulare Fingerabdruckkarten und Verbindungsevidenzen1 |
| **Phase 6: Quarantäne & Gaps-Generierung** | FoodAtlas v4.11 Literatur-Korpus (llm\_extracted)1 | Filterung von unvollständigen Extraktionen ohne Mengenangabe, Organ oder Basis1 | **Regel 5:** Quarantäne in Tier 5 (SRC-UNVERIFIED); Überführung ungelöster Werte1 | *Gaps-Register & Funnel:* Strukturierter Arbeitsvorrat für zukünftige Laboranalytik1 |

Die Überführung dieser Pipeline in eine produktive Systemarchitektur erfordert ein zweistufiges Speichermodell: Sämtliche manuell kuratierten Entitäten (Sortengeschichten, sensorische Attribute, phänologische Kalender und Gaps) werden in versionierten, deklarativen YAML-Dateien geführt1. Die analytischen Massendaten aus FDC Foundation Foods, BioFoodComp 4.0, Phenol-Explorer, FooDB und PTFI werden in spaltenorientierten Parquet-Dateien persistiert und über eine lokale analytische Datenbank (DuckDB) relationiert1. Ein vorgeschalteter Validator prüft vor jedem Build-Prozess die Einhaltung aller Contract-Regeln, verwirft Werte ohne deklarierte Basis und erzeugt die statischen JSON-Payloads für das Frontend1.

Die Realisierung des Food Atlas markiert den methodischen Übergang von einer vereinfachenden, makronutritiven Nährwertkennzeichnung hin zu einer hochauflösenden Kartierung der molekularen Vielfalt unserer Nahrung1. Durch die konsequente ontologische Kopplung agronomischer und botanischer Primärregister wie Mansfeld und Kew WCUPS mit den ausschließlich analytischen Biodiversitätsdaten der FAO BioFoodComp 4.0, den chromatographisch validierten Polyphenolprofilen aus Phenol-Explorer und den nicht-zielgerichteten Multi-Omics-Messungen der Periodic Table of Food Initiative entsteht eine referenzierbare Dateninfrastruktur4. Indem jeder Konzentrationswert zwingend an seine physikalische Bezugsbasis und sein morphologisches Gewebe gebunden wird, eliminiert das System methodische Artefakte früherer Literatur-Mining-Ansätze und schafft ein belastbares Fundament für Ernährungsforschung, bioinformatische Modellierung und nachhaltige Produktentwicklung1.

#### **Referenzen**

> 1. product.md  
> 2. Nutrition \- Dr. Leonardo Riella, [https://leoriella.com/category/blog/nutrition/](https://leoriella.com/category/blog/nutrition/)  
> 3. (PDF) World Checklist of Useful Plant Species \- ResearchGate, [https://www.researchgate.net/publication/342361356\_World\_Checklist\_of\_Useful\_Plant\_Species](https://www.researchgate.net/publication/342361356_World_Checklist_of_Useful_Plant_Species)  
> 4. World Checklist of Useful Plant Species \- KNB, [https://knb.ecoinformatics.org/view/doi:10.5063/F1CV4G34](https://knb.ecoinformatics.org/view/doi:10.5063/F1CV4G34)  
> 5. Guidance on Safety assessment of botanicals, [https://www.aesan.gob.es/fr/dam/jcr:f4c3beb6-4a55-4f7c-b207-b5da8c9b11f6/BOTANICALS\_COMPLEMENTOS\_EFSA\_2009.pdf.pdf](https://www.aesan.gob.es/fr/dam/jcr:f4c3beb6-4a55-4f7c-b207-b5da8c9b11f6/BOTANICALS_COMPLEMENTOS_EFSA_2009.pdf.pdf)  
> 6. Rudolf Mansfeld \- Wikipedia, [https://de.wikipedia.org/wiki/Rudolf\_Mansfeld](https://de.wikipedia.org/wiki/Rudolf_Mansfeld)  
> 7. GBIS: the information system of the German Genebank | Database, [https://academic.oup.com/database/article/doi/10.1093/database/bav021/2433153](https://academic.oup.com/database/article/doi/10.1093/database/bav021/2433153)  
> 8. WORLD ECONOMIC PLANTS, [https://api.pageplace.de/preview/DT0400.9781466576810\_A37766100/preview-9781466576810\_A37766100.pdf](https://api.pageplace.de/preview/DT0400.9781466576810_A37766100/preview-9781466576810_A37766100.pdf)  
> 9. World Economic Plants: A Standard Reference, Second Edition, [https://www.routledge.com/World-Economic-Plants-A-Standard-Reference-Second-Edition/Wiersema-Leon/p/book/9781439821428](https://www.routledge.com/World-Economic-Plants-A-Standard-Reference-Second-Edition/Wiersema-Leon/p/book/9781439821428)  
> 10. FAO/INFOODS food composition database for biodiversity, [https://openknowledge.fao.org/handle/20.500.14283/i7364en](https://openknowledge.fao.org/handle/20.500.14283/i7364en)  
> 11. FAO/INFOODS Food composition database for biodiversity Version 4.0, [https://openknowledge.fao.org/bitstreams/c290dc08-5907-4ef5-831d-c56378aeaede/download](https://openknowledge.fao.org/bitstreams/c290dc08-5907-4ef5-831d-c56378aeaede/download)  
> 12. FoodData Central Foundation Foods Documentation, [https://fdc.nal.usda.gov/Foundation\_Foods\_Documentation](https://fdc.nal.usda.gov/Foundation_Foods_Documentation)  
> 13. FAQs | USDA FoodData Central, [https://fdc.nal.usda.gov/faq](https://fdc.nal.usda.gov/faq)  
> 14. Food Labelling | Food & Nutrition, [https://fnnbri.quadram.ac.uk/labelling/](https://fnnbri.quadram.ac.uk/labelling/)  
> 15. Nutrients | Food & Nutrition: National Bioscience Research, [https://fnnbri.quadram.ac.uk/data/](https://fnnbri.quadram.ac.uk/data/)  
> 16. FooDB, [https://foodb.ca/compliance](https://foodb.ca/compliance)  
> 17. FooDB.ca, [https://foodb.ca/](https://foodb.ca/)  
> 18. Diet and its chemical complexity towards foodome? \- PMC \- NIH, [https://pmc.ncbi.nlm.nih.gov/articles/PMC7161500/](https://pmc.ncbi.nlm.nih.gov/articles/PMC7161500/)  
> 19. Phenol-Explorer: Database on Polyphenol Content in Foods, [http://phenol-explorer.eu/](http://phenol-explorer.eu/)  
> 20. (PDF) Phenol-Explorer: An online comprehensive database on, [https://www.researchgate.net/publication/43352293\_Phenol-Explorer\_An\_online\_comprehensive\_database\_on\_polyphenol\_contents\_in\_foods](https://www.researchgate.net/publication/43352293_Phenol-Explorer_An_online_comprehensive_database_on_polyphenol_contents_in_foods)  
> 21. (PDF) Periodic Table of Food Initiative for generating biomolecular, [https://www.researchgate.net/publication/378843079\_Periodic\_Table\_of\_Food\_Initiative\_for\_generating\_biomolecular\_knowledge\_of\_edible\_biodiversity](https://www.researchgate.net/publication/378843079_Periodic_Table_of_Food_Initiative_for_generating_biomolecular_knowledge_of_edible_biodiversity)  
> 22. Periodic Table of Food Initiative for generating biomolecular, [https://research.wur.nl/en/publications/periodic-table-of-food-initiative-for-generating-biomolecular-kno/](https://research.wur.nl/en/publications/periodic-table-of-food-initiative-for-generating-biomolecular-kno/)  
> 23. FoodOn – FoodOn: A farm to fork ontology, [https://foodon.org/](https://foodon.org/)  
> 24. (PDF) FoodOn: a harmonized food ontology to increase global food, [https://www.researchgate.net/publication/329348621\_FoodOn\_a\_harmonized\_food\_ontology\_to\_increase\_global\_food\_traceability\_quality\_control\_and\_data\_integration](https://www.researchgate.net/publication/329348621_FoodOn_a_harmonized_food_ontology_to_increase_global_food_traceability_quality_control_and_data_integration)  
> 25. TDWG 2000, Abstracts, [https://www.bgbm.org/tdwg/2000/Abstracts/OchsmannEtAl.htm](https://www.bgbm.org/tdwg/2000/Abstracts/OchsmannEtAl.htm)  
> 26. Coriander, Coriandrum sativum L. \- CGSpace, [https://cgspace.cgiar.org/bitstreams/23aa7ed5-6eb8-4503-a6a3-719cdd257cb0/download](https://cgspace.cgiar.org/bitstreams/23aa7ed5-6eb8-4503-a6a3-719cdd257cb0/download)  
> 27. Development and evaluation of a Brassica napus core collection, [https://www.academia.edu/9346035/Development\_and\_evaluation\_of\_a\_Brassica\_napus\_core\_collection](https://www.academia.edu/9346035/Development_and_evaluation_of_a_Brassica_napus_core_collection)  
> 28. World Checklist of Useful Plant Species, [https://kew.iro.bl.uk/lucky-search?index=bl-legacy-id\&value=7243d727-e28d-419d-a8f7-9ebef5b9e03e](https://kew.iro.bl.uk/lucky-search?index=bl-legacy-id&value=7243d727-e28d-419d-a8f7-9ebef5b9e03e)  
> 29. World Checklist of Useful Plant Species 2020 \- ResearchGate, [https://www.researchgate.net/publication/349351241\_World\_Checklist\_of\_Useful\_Plant\_Species\_2020](https://www.researchgate.net/publication/349351241_World_Checklist_of_Useful_Plant_Species_2020)  
> 30. A comprehensive checklist of the wild edible plants of Guinea, [https://ethnobioconservation.com/ebc/article/view/1310](https://ethnobioconservation.com/ebc/article/view/1310)  
> 31. Critonia morifolia (Mill.) R.M.King & H.Rob. \- Useful Plants of Colombia, [https://colplanta.org/taxon/urn:lsid:ipni.org:names:69558-2](https://colplanta.org/taxon/urn:lsid:ipni.org:names:69558-2)  
> 32. A Plant by Any Other Name \- USDA, [https://agresearchmag.ars.usda.gov/ar/archive/2001/mar/plant0301.pdf](https://agresearchmag.ars.usda.gov/ar/archive/2001/mar/plant0301.pdf)  
> 33. 2022 Crop Germplasm Committee Chairs Virtual Meeting March 3, [https://www.ars-grin.gov/documents/cgc/briefings/2022%20CGC%20Chairs%20meeting%20presentations.pdf](https://www.ars-grin.gov/documents/cgc/briefings/2022%20CGC%20Chairs%20meeting%20presentations.pdf)  
> 34. Bobgunnia J. H. Kirkbr. & Wiersema \- Search Accessions GRIN-Global, [https://ausgenebank.agriculture.vic.gov.au/gringlobal/taxonomygenus.aspx?id=18356](https://ausgenebank.agriculture.vic.gov.au/gringlobal/taxonomygenus.aspx?id=18356)  
> 35. Legume Crops Phylogeny and Genetic Diversity for Science ... \- Pure, [https://pure-oai.bham.ac.uk/ws/files/117979488/Legume\_Crops\_Phylogeny\_and\_Genetic\_Diversity\_for\_Science\_and\_Breeding.pdf](https://pure-oai.bham.ac.uk/ws/files/117979488/Legume_Crops_Phylogeny_and_Genetic_Diversity_for_Science_and_Breeding.pdf)  
> 36. Cornucopia II \- A source book of edible plants \- Bookis, [https://bookis.com/en-no/books/stephen-facciola-cornucopia-ii-a-source-book-of-edible-plants-1998](https://bookis.com/en-no/books/stephen-facciola-cornucopia-ii-a-source-book-of-edible-plants-1998)  
> 37. Cornucopia II: a source book of edible plants \- World Vegetable Center, [https://worldveg.tind.io/record/25818](https://worldveg.tind.io/record/25818)  
> 38. Cornucopia II now back in print\! \- books \- Permies.com, [https://permies.com/t/51809/Cornucopia-II-print](https://permies.com/t/51809/Cornucopia-II-print)  
> 39. Cornucopia II: A Source Book of Edible Plants by Stephen Facciola, [https://wildfoodadventures.com/cornucopia-ii-a-source-book-of-edible-plants-by-stephen-facciola/](https://wildfoodadventures.com/cornucopia-ii-a-source-book-of-edible-plants-by-stephen-facciola/)  
> 40. Buy Temperate Plant Database \- Plants For A Future, [https://plantsforafuture.com/buy-temperate-plant-database/](https://plantsforafuture.com/buy-temperate-plant-database/)  
> 41. PFAF database to .csv / .xlsx : r/Permaculture \- Reddit, [https://www.reddit.com/r/Permaculture/comments/10eimqx/pfaf\_database\_to\_csv\_xlsx/](https://www.reddit.com/r/Permaculture/comments/10eimqx/pfaf_database_to_csv_xlsx/)  
> 42. Plants For A Future (PFAF) API \- Parse.bot, [https://parse.bot/marketplace/4e78b490-23c9-4f6e-9d81-211259d99548/plantsforafuture-org-api](https://parse.bot/marketplace/4e78b490-23c9-4f6e-9d81-211259d99548/plantsforafuture-org-api)  
> 43. Castilleja linariaefolia Wyoming Indian Paintbrush PFAF Plant, [https://pfaf.org/user/Plant.aspx?LatinName=Castilleja%20linariaefolia](https://pfaf.org/user/Plant.aspx?LatinName=Castilleja+linariaefolia)  
> 44. Service Tree, Sorb Apple | Sorbus domestica \- PFAF.org, [https://pfaf.org/plants/service-tree-sorb-apple-sorbus-domestica/](https://pfaf.org/plants/service-tree-sorb-apple-sorbus-domestica/)  
> 45. Plants For A Future Shop \- PFAF.org, [https://pfaf.org/user/cmspage.aspx?pageid=31](https://pfaf.org/user/cmspage.aspx?pageid=31)  
> 46. Pouteria campechiana (PROSEA) \- Pl@ntUse \- PlantNet, [https://plantuse.plantnet.org/en/Pouteria\_campechiana\_(PROSEA)](https://plantuse.plantnet.org/en/Pouteria_campechiana_\(PROSEA\))  
> 47. Grewia bicolor (PROTA) \- Pl@ntUse, [https://uses.plantnet-project.org/en/Grewia\_bicolor\_(PROTA)](https://uses.plantnet-project.org/en/Grewia_bicolor_\(PROTA\))  
> 48. Java almond, Canarium indicum, GALIP NUT/ Alternative Medicine, [https://www.stuartxchange.org/JavaAlmond](https://www.stuartxchange.org/JavaAlmond)  
> 49. FAO/INFOODS Food Composition Table for Western Africa (2019, [https://openknowledge.fao.org/handle/20.500.14283/ca7779b](https://openknowledge.fao.org/handle/20.500.14283/ca7779b)  
> 50. An indicator of the conservation status of useful wild plants, [https://alliancebioversityciat.org/indicator-conservation-status-useful-wild-plants](https://alliancebioversityciat.org/indicator-conservation-status-useful-wild-plants)  
> 51. Mapping Asia Plants: Plant Diversity and a Checklist of Vascular, [https://www.mdpi.com/2223-7747/13/16/2281](https://www.mdpi.com/2223-7747/13/16/2281)  
> 52. Cornucopia II: A Source Book of Edible Plants \- ISBN 9780962808722, [https://www.campusbooks.com/books/9780962808722-cornucopia-ii-a-source-book-of-edible-plants](https://www.campusbooks.com/books/9780962808722-cornucopia-ii-a-source-book-of-edible-plants)  
> 53. Bolboschoenus maritimus Cosmopolitan Bulrush PFAF Plant, [https://pfaf.org/user/Plant.aspx?LatinName=Bolboschoenus%20maritimus](https://pfaf.org/user/Plant.aspx?LatinName=Bolboschoenus+maritimus)  
> 54. Food Catalogue — CNF \+ WAFCT \+ FDC \- EcoDish365, [https://ecodish365.com/cnf](https://ecodish365.com/cnf)  
> 55. Free Macro Reference Tables: CSV & JSON Nutrition Data Download, [https://nutrola.app/en/blog/free-macro-reference-tables-csv-json-download](https://nutrola.app/en/blog/free-macro-reference-tables-csv-json-download)  
> 56. McCance and Widdowson's The Composition of Foods Seventh, [https://www.researchgate.net/publication/272241154\_McCance\_and\_Widdowson's\_The\_Composition\_of\_Foods\_Seventh\_Summary\_Edition\_and\_updated\_Composition\_of\_Foods\_Integrated\_Dataset](https://www.researchgate.net/publication/272241154_McCance_and_Widdowson's_The_Composition_of_Foods_Seventh_Summary_Edition_and_updated_Composition_of_Foods_Integrated_Dataset)  
> 57. Nutritics GB23 database: an enhancement of the McCance, [https://www.cambridge.org/core/journals/proceedings-of-the-nutrition-society/article/nutritics-gb23-database-an-enhancement-of-the-mccance-widdowsons-the-composition-of-foods-integrated-dataset-cofid-database/78EFC02D103180C115AF634CA347A561](https://www.cambridge.org/core/journals/proceedings-of-the-nutrition-society/article/nutritics-gb23-database-an-enhancement-of-the-mccance-widdowsons-the-composition-of-foods-integrated-dataset-cofid-database/78EFC02D103180C115AF634CA347A561)  
> 58. Meet the experts, [https://www.fao.org/indigenous-peoples/secretariats/global-hub/meet-the-experts/en](https://www.fao.org/indigenous-peoples/secretariats/global-hub/meet-the-experts/en)  
> 59. Indigenous Peoples' food systems:, [https://www.fao.org/4/i0370e/i0370e00.pdf](https://www.fao.org/4/i0370e/i0370e00.pdf)  
> 60. Commentary: Indigenous peoples' food and environment, [https://worldnutritionjournal.org/wn/article/download/376/322/795](https://worldnutritionjournal.org/wn/article/download/376/322/795)  
> 61. DOCUMENTING TRADITIONAL FOOD SYSTEMS OF INDIGENOUS, [https://www.mcgill.ca/cine/sites/cine/files/manual.pdf](https://www.mcgill.ca/cine/sites/cine/files/manual.pdf)  
> 62. Indigenous Peoples' food systems and well-being: interventions and, [https://www.fao.org/4/i3144e/I3144e00.pdf](https://www.fao.org/4/i3144e/I3144e00.pdf)  
> 63. Indigenous Peoples' food systems: \- ResearchGate, [https://www.researchgate.net/profile/Harriet-Kuhnlein/publication/236035671\_Indigenous\_peoples'\_food\_systems\_the\_many\_dimensions\_of\_culture\_diversity\_and\_environment\_for\_nutrition\_and\_health/links/555252ab08ae980ca606adb3/Indigenous-peoples-food-systems-the-many-dimensions-of-culture-diversity-and-environment-for-nutrition-and-health.pdf](https://www.researchgate.net/profile/Harriet-Kuhnlein/publication/236035671_Indigenous_peoples'_food_systems_the_many_dimensions_of_culture_diversity_and_environment_for_nutrition_and_health/links/555252ab08ae980ca606adb3/Indigenous-peoples-food-systems-the-many-dimensions-of-culture-diversity-and-environment-for-nutrition-and-health.pdf)  
> 64. Chemical Complexity of Food and Implications for Therapeutics \- PMC, [https://pmc.ncbi.nlm.nih.gov/articles/PMC12674684/](https://pmc.ncbi.nlm.nih.gov/articles/PMC12674684/)  
> 65. (PDF) Decoding the Foodome: Molecular Networks Connecting Diet, [https://www.researchgate.net/publication/375665637\_Decoding\_the\_Foodome\_Molecular\_Networks\_Connecting\_Diet\_and\_Health](https://www.researchgate.net/publication/375665637_Decoding_the_Foodome_Molecular_Networks_Connecting_Diet_and_Health)  
> 66. Decoding the Foodome: Molecular Networks Connecting Diet and, [https://barabasi.com/media/2024-Menichetti-Decoding.pdf](https://barabasi.com/media/2024-Menichetti-Decoding.pdf)  
> 67. ncbitaxon \- KG-Registry, [https://kghub.org/kg-registry/resource/ncbitaxon/ncbitaxon.html](https://kghub.org/kg-registry/resource/ncbitaxon/ncbitaxon.html)  
> 68. Dashboard Week, Day 2: 80 Grams — Where Your Daily Fat Really, [https://www.thedataschool.co.uk/mila-kholodiy/dashboard-week-day-2-80-grams-where-your-daily-fat-really-comes-from/](https://www.thedataschool.co.uk/mila-kholodiy/dashboard-week-day-2-80-grams-where-your-daily-fat-really-comes-from/)  
> 69. Downloads \- FooDB, [https://foodb.ca/downloads](https://foodb.ca/downloads)  
> 70. Phenol-Explorer: an online comprehensive database on polyphenol, [https://pmc.ncbi.nlm.nih.gov/articles/PMC2860900/](https://pmc.ncbi.nlm.nih.gov/articles/PMC2860900/)  
> 71. Methods Used To Create Phenol-Explorer, [http://phenol-explorer.eu/methods\_used](http://phenol-explorer.eu/methods_used)  
> 72. Frequently Asked Questions (FAQ) \- Phenol-Explorer, [http://phenol-explorer.eu/faqs](http://phenol-explorer.eu/faqs)  
> 73. Development of an Unified Food Composition Database for the, [https://d-nb.info/1247667790/34](https://d-nb.info/1247667790/34)  
> 74. a major update of the Phenol-Explorer database to incorporate data, [https://academic.oup.com/database/article/doi/10.1093/database/bat070/342410](https://academic.oup.com/database/article/doi/10.1093/database/bat070/342410)  
> 75. Periodic Table of Food Initiative for generating biomolecular, [https://worldveg.tind.io/record/76037/files/Jarvis%20et%20al\_2024\_Periodic%20Table%20of%20Food%20Initiative.pdf](https://worldveg.tind.io/record/76037/files/Jarvis%20et%20al_2024_Periodic%20Table%20of%20Food%20Initiative.pdf)  
> 76. Periodic Table of Food Initiative for generating biomolecular, [https://worldveg.tind.io/record/76037](https://worldveg.tind.io/record/76037)  
> 77. Breakthrough Research \- UC Davis Innovation Institute for Food and, [https://foodandhealth.ucdavis.edu/breakthrough-research/](https://foodandhealth.ucdavis.edu/breakthrough-research/)  
> 78. Downloads \- Phenol-Explorer, [http://phenol-explorer.eu/downloads](http://phenol-explorer.eu/downloads)  
> 79. Language Model Analysis for Ontology Subsumption Inference, [https://www.researchgate.net/publication/368507896\_Language\_Model\_Analysis\_for\_Ontology\_Subsumption\_Inference](https://www.researchgate.net/publication/368507896_Language_Model_Analysis_for_Ontology_Subsumption_Inference)  
> 80. FoodOn: a harmonized food ontology to increase global ... \- PMC \- NIH, [https://pmc.ncbi.nlm.nih.gov/articles/PMC6550238/](https://pmc.ncbi.nlm.nih.gov/articles/PMC6550238/)  
> 81. FoodOn Relations, [https://foodon.org/design/foodon-relations/](https://foodon.org/design/foodon-relations/)  
> 82. FoodOn and Anatomy, [https://foodon.org/foodon-and-anatomy/](https://foodon.org/foodon-and-anatomy/)  
> 83. Extending FAIR to FAIREr: Cognitive Interoperability and the Human, [https://www.researchgate.net/publication/367049744\_Extending\_FAIR\_to\_FAIREr\_Cognitive\_Interoperability\_and\_the\_Human\_Explorability\_of\_Data\_and\_Metadata](https://www.researchgate.net/publication/367049744_Extending_FAIR_to_FAIREr_Cognitive_Interoperability_and_the_Human_Explorability_of_Data_and_Metadata)  
> 84. OBO Foundry Food Ontology Interconnectivity \- Semantic Web Journal, [https://www.semantic-web-journal.net/system/files/swj3458.pdf](https://www.semantic-web-journal.net/system/files/swj3458.pdf)  
> 85. Improving annotation, access, and comparison of nutritional, [https://academic.oupdev.silverchair.com/database/article/doi/10.1093/database/baag050/8769951](https://academic.oupdev.silverchair.com/database/article/doi/10.1093/database/baag050/8769951)