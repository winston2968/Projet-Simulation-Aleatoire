
install.packages(c("tidyverse", "hexbin", "gganimate", "viridis", "gifski"))

library(tidyverse)
library(viridis)
library(gganimate)

plot(test$time_step, test$temperature_k, col='green', main='temperature au cours du tps')

plot(test2$time_step, test2$temperature_k, col='green')
summary(reacteur_1000)
summary(traj_neutrons)

boxplot(reacteur_1000$pos_RE01, main = "Diagramme du placement en pourcentage en profondeur des barres de controles", ylab = "Pourcentage en profondeur", col = "green")

plot(reacteur_1000$power_mw,reacteur_1000$pos_RE01)

plot(reacteur_1000$time_step,reacteur_1000$temperature_k)
plot(reacteur_1000$time_step,reacteur_1000$pos_RE01)
plot(reacteur_1000$time_step,reacteur_1000$power_mw)






library(tidyverse)
library(gganimate)

# Simulation de vos données (pour que l'exemple soit reproductible)
df <- data.frame(
  time_step = rep(0:5, each = 200),
  neutron_id = 1:10000,
  # On simule deux zones pour l'exemple
  x = c(rnorm(600, mean=10, sd=3), rnorm(600, mean=5, sd=3)),
  y = c(rnorm(600, mean=10, sd=3), rnorm(600, mean=5, sd=3)),
  type = sample(c("fast", "epithermal"), 10000, replace = TRUE)
)

# On filtre pour un seul pas de temps (ex: time_step 0) pour commencer
df_t0 <- df %>% filter(time_step == 0)

ggplot(df, aes(x = x, y = y)) +
  # On utilise bin2d pour compter les neutrons dans des carrés
  geom_bin2d(bins = 30) + 
  
  # Palette de couleurs "Magma" (très lisible pour la chaleur/densité)
  scale_fill_viridis_c(option = "magma") +
  
  # SÉPARATION MAGIQUE : On crée un graphe par type de neutron
  facet_wrap(~ type) + 
  
  coord_fixed() +
  theme_minimal() +
  labs(title = "Distribution spatiale : Rapides vs Épithermiques",
       fill = "Densité")
