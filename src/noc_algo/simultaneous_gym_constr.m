close all; clear; clc;
import casadi.*;

%% initial

% parameters
nx = 2;         % state dimension
nu = 1;         % control dimension
N = 50;         % horizon length
DT = .1;        % discretization time step
N_rk4 = 10;     % number of rk4 steps per discretiazion time step
x0bar = [pi; 0];   % initial state

% build integrator
% dynamics
dynamics = @(x,u) [x(2); sin(x(1)) + u];
h = DT / N_rk4;             % integration step
x = MX.sym('x',nx,1);
u = MX.sym('u',nu,1);

x_next = x;
for i = 1:N_rk4
    x_next = rk4step(x_next, u, dynamics, h);
end

% integrator
F = Function('F',{x, u}, {x_next});

%% NLP formulation


% collect all decision variables in w
g = [];

w = {};
ubw = [];

w0 = 0.1;
L = 0;

X_k = x0bar;

for i = 1:N
    U_k = MX.sym(['U_',num2str(i)],   nu, 1);
    ubw = [ubw; 2];
    L = L + X_k(1)^2 + 0.1*X_k(2)^2;
    L = L + 0.01 * sum(U_k.^2);

    X_next = F(X_k, U_k);
    
    X_k = MX.sym(['X_',num2str(i+1)], nx, 1);
    ubw = [ubw; inf; 8];
    w = {w{:}, U_k};
    w = {w{:}, X_k};
    g = [g; X_next - X_k];
end

L = L + 10 * sum(X_k.^2);

% create nlp solver
nlp = struct('x', vertcat(w{:}), 'f', L, 'g', g);
solver = nlpsol('solver','ipopt', nlp);

% solve nlp
sol = solver('x0', w0, 'lbx', -ubw, 'ubx', ubw, 'lbg', 0, 'ubg', 0);

%% visualize solution

w_opt = full(sol.x);
U_opt = w_opt(1:nx+nu:end);
X_opt = [w_opt(2:nx+nu:end)';...
         w_opt(3:nx+nu:end)'];

X_opt = [x0bar, X_opt];

figure(2); clf;
subplot(2,1,1); hold on;
plot(0:N, X_opt(1,:))
plot(0:N, X_opt(2,:))
title('state trajectory')
legend('\phi', '\omega')

subplot(2,1,2); hold on;
stairs(0:N, [full(U_opt); nan])
title('control trajectory')
legend('\tau')
xlabel('discrete time k')