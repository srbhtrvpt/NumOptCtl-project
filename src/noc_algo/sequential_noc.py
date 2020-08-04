import numpy as np
from casadi import *
import math
import matplotlib.pyplot as plt
from pendulum_dynamics import PendulumDynamics
from pendulum import PendulumEnv
import time


def extractSolFromNlpSolver(res):
    w_opt = res["x"]
    w_opt_np = np.array(w_opt)
    # print(w_opt_np.shape)
    u_opt = []
    th_opt = []
    thdot_opt = []
    for i in range(0, w_opt_np.shape[0], 3):
        u_opt.append(w_opt_np[i])
        th_opt.append(w_opt_np[i+1])
        thdot_opt.append(w_opt_np[i+2])
    u_opt = np.array(u_opt)
    th_opt = np.array(th_opt)
    thdot_opt = np.array(thdot_opt)
    print('u_opt shape:', {u_opt.shape})
    print('th_opt shape:', {th_opt.shape})
    print('thdot_opt shape:', {thdot_opt.shape})
    return u_opt, th_opt, thdot_opt

if __name__ == '__main__':

    pend_dyn = PendulumDynamics()

    #parameters
    nx = 2          # state dimension
    nu = 1          # control dimension
    N = 100         # horizon length
    x0bar = [np.pi, 0]    # initial state
    max_speed = pend_dyn.max_speed
    max_torque = pend_dyn.max_torque

    x = MX.sym('x',nx,1) 
    u = MX.sym('u',nu,1) 


    x_next = pend_dyn.simulate_next_state(x, u) 
    print('type x_next:', type(x_next))
    # integrator
    F = Function('F', [x, u], [x_next], \
                ['x', 'u'], ['x_next']) 
    print('F:', F)

    # NLP formulation
    # collect all decision variables in w
    g = [] 
    # full state vector w: [u0, theta1, omega1, ....u49, theta50, omega50]
    w = [] 
    # constraint on the entire state vector
    ubw = [] 
    w0 = 0.1 
    L = 0 
    X_k = x0bar 

    for i in range(N):
        U_name = 'U_' + str(i)
        U_k = MX.sym(U_name, nu, 1) 
        L += X_k[0]**2 + 0.1*(X_k[1])**2 + 0.001*U_k**2 

        X_next = F(X_k, U_k) 

        X_name = 'X_' + str(i+1)
        X_k = MX.sym(X_name, nx, 1) 

        ubw = vertcat(ubw, max_torque, inf, max_speed)
        w = vertcat(w, U_k, X_k)
        g = vertcat(g, X_next - X_k)
    L += 10*(X_k[0]**2.0 + X_k[1]**2.0) 
    # print the dimensions
    print("w shape:" ,np.shape(w), 'g shape:' ,np.shape(g), 'ubw shape:', np.shape(ubw))
    # create nlp solver
    nlp = {"x": w,
           "f": L,
           "g": g}
    solver = nlpsol('solver','ipopt', nlp) 

    arg = {}
    arg["x0"] = w0
    arg["lbx"] = -ubw
    arg["ubx"] = ubw
    arg["lbg"] = 0
    arg["ubg"] = 0

    # Solve the problem
    res = solver(**arg)

    # visualise solution
    u_opt, th_opt, thdot_opt = extractSolFromNlpSolver(res)

    fig, (ax1, ax2) = plt.subplots(2, 1, sharex=True)
    ax1.plot(th_opt)
    ax1.plot(thdot_opt)
    ax2.plot(u_opt)
    plt.show()

    env = PendulumEnv()
    #state = []
    s = env.reset()
    for i in range(N):
        env.render()
        s, _, d, _ = env.step(u_opt[i])
        #state.append(s)
        time.sleep(0.1)
    #plt.plot(state)

