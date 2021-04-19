import random
import time

class q_learning:
    LEARNING_RATE = 0.7 # Constant Learning rate
    DISCOUNT_RATE = 0.99 # Discount Rate
    EPSILON = 0.001

    def __init__(self):
        self.Q_table = {}

    def max_Qvalue(self, state):
        max_Qvalue = max(self.Q_table[state])
        action = self.Q_table[state].index(max_Qvalue)

        if random.random() < self.EPSILON:
            action = int(not action)
            max_Qvalue = self.Q_table[state][action]
        return action, max_Qvalue

    def append_state(self, state):
        # Add state to Q table if not already added
        if state not in self.Q_table:
            self.Q_table[state]=[]
            self.Q_table[state].append(0)
            self.Q_table[state].append(0)

    def update_Q_table(self, bird_tuple, crashed, score):
        bird_tuple.reverse() # Reverse the list of experiences

        # If crashed with upper pipe then tax the last jump that caused it
        if crashed:
            for i, x in enumerate(bird_tuple):
                if x[1]==1:
                    temp = list(bird_tuple[i])
                    temp[2] = -15
                    bird_tuple[i] = tuple(temp)
                    break
        # For each entry calculate and update Q value
        for part in bird_tuple:
            current_state = part[0]
            action = part[1]
            reward = part[2]
            _, future_state = self.max_Qvalue(part[3])
            self.Q_table[current_state][action] = (1 - self.LEARNING_RATE) * self.Q_table[current_state][action] + self.LEARNING_RATE * (reward + self.DISCOUNT_RATE * future_state)
