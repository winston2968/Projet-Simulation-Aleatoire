
test <- read.csv("~/PROJET/Projet-Simulation-Aleatoire/statistics/statistics_output/reactor_history_2025_11_26_13_04_58.csv")
plot(test$time_step, test$temperature_k, col='green', main='temperature au cours du tps')

test2 <- read.csv("~/PROJET/Projet-Simulation-Aleatoire/simulation_results/neutrons_trajectories_2025-11-25_23-30-22.csv")
library(ggplot2)
subset_t50 <- subset(test2, time_step == 50)
ggplot(subset_t50, aes(x=x, y=y, color=type)) + geom_point()
