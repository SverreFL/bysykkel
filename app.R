library(dplyr)
library(leaflet)
library(sf)
library(readr)
library(glue)
library(purrr)
library(bslib)

stations <- read_csv("resources/data/stations.csv")
trips <- read_csv("resources/data/trips.csv") %>%
  rename(from = `...1`,
         to = `1`)

paths <- st_read("resources/geometry/geometries_new.geojson")

trips_paths <- trips %>% 
  left_join(paths) %>% 
  left_join(
    stations %>% 
      select(start_station_id,
             start_name = name),
    join_by(from == start_station_id)
    ) %>% 
  left_join(
    stations %>% 
      select(start_station_id,
             end_name = name,
             end_longitude = longitude,
             end_latitude = latitude),
    join_by(to == start_station_id)
  ) %>% 
  mutate(num_trips_binned = cut(num_trips,
                                breaks = quantile(num_trips, probs = seq(0, 1, 0.1)),
                                labels = FALSE),
         num_trips_binned = tidyr::replace_na(num_trips_binned, 1),
         num_trips_binned = if_else(num_trips == 0, 0, num_trips_binned)
         ) %>% 
  sf::st_as_sf()
  

  



green <- "#008a34"
tiles_url <- "https://api.mapbox.com/styles/v1/svlan/clowzjqm6010u01o41ngl6vnm/tiles/256/{z}/{x}/{y}@2x?access_token=pk.eyJ1Ijoic3ZsYW4iLCJhIjoiY2xvd3poem05MDEyMDJpcDgxamR4b2ZvbSJ9.LFIFyDd8pHDJl0RDksgOsA"


library(shiny)

  ui <- page_fillable(
    class = "p-0",
    absolutePanel(
      style = "z-index: 1",
      top = "10px",
      right = "10px",
      tooltip(bsicons::bs_icon(
        "info-circle", size = "40px"),
        "Visualisering av reisemønster for bysyklene i 2020. Jeg har forsøkt å finne korteste
        vei mellom alle stasjonene og tykkelsen på linjene avhenger av antall turer.")),
    leafletOutput("m", width = "100%", height = "100%")
)

server <- function(input, output, session) {
  
  output$m <- renderLeaflet({
    stations %>% 
      leaflet() %>% 
      addTiles(urlTemplate = tiles_url) %>% 
      addCircleMarkers(
        color = green,
        radius = 5,
        opacity = 1,
        weight = 4,
        label = ~name,
        group = "stations",
        layerId = ~start_station_id
      ) 
      
  })
  
  observe({
    akt_station_id = input$m_marker_click$id
    
    akt_paths <- trips_paths %>% 
      filter(from == akt_station_id) %>% 
      mutate(lab = glue("{end_name}<br>Antall turer: {num_trips}"))
  
    leafletProxy("m") %>% 
      clearShapes() %>% 
      addCircleMarkers(
        data = akt_paths,
        lat = ~end_latitude,
        lng = ~end_longitude,
        color = green,
        radius = 5,
        opacity = 1,
        weight = 4,
        label = map(akt_paths$lab, htmltools::HTML),
        group = "stations",
        layerId = ~to
      ) %>% 
      addPolylines(data=akt_paths$geometry,
                   color = "black",
                   # opacity = ~num_trips_binned*0.1+0.5,
                   # weight = ~num_trips_binned*0.2+0.3
                   ) 
  }) %>% 
    bindEvent(input$m_marker_click)
}

shinyApp(ui, server)
