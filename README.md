Kode for to webapper som visualiserer  [data](https://bergenbysykkel.no/apne-data/historisk) fra i overkant av én million reiser med [Bergen Bysykkel](https://bergenbysykkel.no/) i 2020.
1. [Applikasjon i Voilà](https://bysykkel-voila.herokuapp.com/) som for hver stasjon viser antall reiser og gjennomsnittlig reisetid til alle de andre stasjonene.
2. [Applikasjon i Panel](https://bysykkel-panel.herokuapp.com/main) som for hver stasjon viser gjennomsnitllig antall reiser til og fra for hver time av dagen.

Jeg måtte bruke [Voilà](https://github.com/voila-dashboards/voila) til den ene applikasjonen fordi [Panel](https://panel.holoviz.org/) har begrenset støtte for [Ipyleaflet](https://ipyleaflet.readthedocs.io/en/latest/) som er brukt til å lage interaktivt kart i begge applikasjonene. 

