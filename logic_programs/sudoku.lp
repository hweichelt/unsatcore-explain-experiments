% ########### SUDOKU SOLVER ###########

% GENERATING

number(1..4).

% Transfer initial values to sudoku
sudoku(X,Y,V) :- initial(X,Y,V).
% Generate sudoku Values
{sudoku(X,Y,N): number(N)}=1 :- number(X) ,number(Y).
% Generate Cage Variables for lookup
cage(X1,Y1,X2,Y2):- sudoku(X1,Y1,_), sudoku(X2,Y2,_), ((X1-1)/2)==((X2-1)/2), ((Y1-1)/2)==((Y2-1)/2).

% INTEGRITY CONSTRAINTS

% Unique Numbers in X-Direction
:- sudoku(X,Y1,N), sudoku(X,Y2,N), Y1 != Y2.
% Unique Numbers in Y-Direction
:- sudoku(X1,Y,N), sudoku(X2,Y,N), X1 != X2.
% Unique Numbers in cage
:- cage(X1,Y1,X2,Y2), sudoku(X1,Y1,N), sudoku(X2,Y2,N), X1!=X2, Y1!=Y2.

#show sudoku/3.