
test <- read.csv("~/PROJET/Projet-Simulation-Aleatoire/statistics/statistics_output/reactor_history_2025_11_26_22_03_40.csv")




plot(test$time_step, test$temperature_k, col='green', main='temperature au cours du tps')

plot(test2$time_step, test2$temperature_k, col='green')
