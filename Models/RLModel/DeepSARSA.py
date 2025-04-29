
# import tensorflow as tf
# import numpy as np
# import random
# from tensorflow.keras.layers import Dense
# from tensorflow.keras.optimizers import Adam

# # 딥살사 인공신경망
# class DeepSARSA(tf.keras.Model):
#     def __init__(self, action_size):
#         super(DeepSARSA, self).__init__()
#         self.fc1 = Dense(30, activation='relu')
#         self.fc2 = Dense(30, activation='relu')
#         self.fc_out = Dense(action_size)

#     def call(self, x):
#         x = self.fc1(x)
#         x = self.fc2(x)
#         q = self.fc_out(x)
#         return q

# # 딥살사 에이전트
# class DeepSARSAgent:
#     def __init__(self, state_size, action_size):
#         # 상태의 크기와 행동의 크기 정의
#         self.state_size = state_size
#         self.action_size = action_size
        
#         # 딥살사 하이퍼 파라메터
#         self.discount_factor = 0.99
#         self.learning_rate = 0.001
#         self.epsilon = 1.  
#         self.epsilon_decay = 0.999999 #0.9999999 
#         self.epsilon_min = 0.01
#         self.model = DeepSARSA(self.action_size)
#         self.optimizer = Adam(learning_rate=self.learning_rate)

#     # 입실론 탐욕 정책으로 행동 선택
#     def getAction(self, state, actionList):
#         if np.random.rand() <= self.epsilon:
#             return random.randrange(len(actionList))
#         else:
#             q_values = self.model(state)
#             if len(actionList) == 1:
#                 mask = [0, -99999]
#             else:
#                 mask = [0, 0]
#             maskedReturn = np.argmax(q_values[0] + mask)
#             return maskedReturn

#     # <s, a, r, s', a'>의 샘플로부터 모델 업데이트
#     def train_model(self, state, action, reward, next_state, next_action, done):
#         if self.epsilon > self.epsilon_min:
#             self.epsilon *= self.epsilon_decay

#         # 학습 파라메터
#         model_params = self.model.trainable_variables
#         with tf.GradientTape() as tape:
#             tape.watch(model_params)
#             predict = self.model(state)[0]
#             one_hot_action = tf.one_hot([action], self.action_size)
#             predict = tf.reduce_sum(one_hot_action * predict, axis=1)

#             # done = True 일 경우 에피소드가 끝나서 다음 상태가 없음
#             next_q = self.model(next_state)[0][next_action]
#             target = reward + (1 - done) * self.discount_factor * next_q

#             # MSE 오류 함수 계산
#             # loss = tf.reduce_mean(tf.square(target - predict))
#             print("\n")
#             print(predict)
#             print(target)
#             loss = tf.reduce_mean(tf.square(target - predict))
#             print(loss)
        
#         # 오류함수를 줄이는 방향으로 모델 업데이트
#         grads = tape.gradient(loss, model_params)
#         self.optimizer.apply_gradients(zip(grads, model_params))
