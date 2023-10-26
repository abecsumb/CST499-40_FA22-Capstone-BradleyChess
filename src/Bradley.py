import Environ
import Agent
import Settings
import re
from helper_methods import *
import chess
import chess.engine
import pandas as pd
import copy
# import logging
# import log_config
# logger = logging.getLogger(__name__)

print_debug_statements_filepath = r'C:\Users\Abrah\Dropbox\PC (2)\Desktop\GitHub Repos\CST499-40_FA22-Capstone-BradleyChess\debug\BRADLEY_print_statements.txt'
PRINT_RESULTS_DEBUG: bool = True
if PRINT_RESULTS_DEBUG:
    print_statements_debug = open(print_debug_statements_filepath, 'a')

error_log_filepath = r'C:\Users\Abrah\Dropbox\PC (2)\Desktop\GitHub Repos\CST499-40_FA22-Capstone-BradleyChess\debug\BRADLEY_error_log.txt'
error_log = open(error_log_filepath, 'a')

class Bradley:
    """Acts as the single point of communication between the RL agent and the player.
    This class trains the agent and helps to manage the chessboard during play between the computer and the user.
    This is a composite class with members of the Environ class and the Agent class.

    Args:
        chess_data (pd.DataFrame): A Pandas DataFrame containing the chess data.
    Attributes:
        chess_data (pd.DataFrame): A Pandas DataFrame containing the chess data.
        settings (Settings.Settings): A Settings object containing the settings for the RL agents.
        environ (Environ.Environ): An Environ object representing the chessboard environment.
        W_rl_agent (Agent.Agent): A white RL Agent object.
        B_rl_agent (Agent.Agent): A black RL Agent object.
            engine (chess.engine.SimpleEngine): A Stockfish engine used to analyze positions during training.
    """
    def __init__(self, chess_data: pd.DataFrame):

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley Constructor ==========\n\n")

        self.chess_data = chess_data
        self.settings = Settings.Settings()
        self.environ = Environ.Environ(self.chess_data)
        self.W_rl_agent = Agent.Agent('W', self.chess_data)             
        self.B_rl_agent = Agent.Agent('B', self.chess_data)
  
        self.W_rl_agent.settings.learn_rate = 0.6
        self.W_rl_agent.settings.discount_factor = 0.3

        self.B_rl_agent.settings.learn_rate = 0.2
        self.B_rl_agent.settings.discount_factor = 0.8

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'White agent learn rate is: {self.W_rl_agent.settings.learn_rate}\n')
            print_statements_debug.write(f'White agent discount factor is: {self.W_rl_agent.settings.discount_factor}\n') 
            print_statements_debug.write(f'Black agent learn rate is: {self.B_rl_agent.settings.learn_rate}\n')
            print_statements_debug.write(f'Black agent discount factor is: {self.B_rl_agent.settings.discount_factor}\n')

        # stockfish is used to analyze positions during training
        # this is how we estimate the q value at each position, 
        # and also for anticipated next position
        self.engine = chess.engine.SimpleEngine.popen_uci(self.settings.stockfish_filepath)

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== End of Bradley Constructor ==========\n\n\n")

    # @log_config.log_execution_time_every_N()
    def recv_opp_move(self, chess_move: str) -> bool:                                                                                 
        """Receives the opponent's chess move and loads it onto the chessboard.
        Call this method when the opponent makes a move. This method assumes that the incoming chess move is valid and playable.

        Args:
            chess_move (str): A string representing the opponent's chess move, such as 'Nf3'.
        Returns:
            bool: A boolean value indicating whether the move was successfully loaded.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.recv_opp_move ==========\n\n")

        # load_chessboard returns False if failure to add move to board,
        if self.environ.load_chessboard(chess_move):
            # loading the chessboard was a success, now just update the curr state
            self.environ.update_curr_state()

            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Chessboard was successfully loaded with move: {chess_move}\n')
                print_statements_debug.write(f'Chessboard looks like this:\n\n')
                print_statements_debug.write(f'\n {self.environ.board}\n\n')
                print_statements_debug.write(f'Current turn is: {self.environ.get_curr_turn()}\n')
                print_statements_debug.write(f'Current turn index is: {self.environ.turn_index}\n')
                print_statements_debug.write("Bye from Bradley.recv_opp_move\n\n\n")

            return True
        else:
            error_log.write(f'Error: failed to load chessboard with move: {chess_move}\n')
            error_log.write("========== Bye from Bradley.recv_opp_move ==========\n\n\n")
            return False
    ### end of recv_opp_move ###

    # @log_config.log_execution_time_every_N()
    def rl_agent_selects_chess_move(self, rl_agent_color: str) -> dict[str]:
        """Selects a chess move for the RL agent and loads it onto the chessboard.
        Call this method when the RL agent selects a move. This method assumes that the agents have already been trained.

        Args:
            rl_agent_color (str): A string indicating the color of the RL agent, either 'W' or 'B'.
        Returns:
            dict[str]: A dictionary containing the selected chess move string.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.rl_agent_selects_chess_move ==========\n\n")

        if rl_agent_color == 'W':
            chess_move: dict[str] = self.W_rl_agent.choose_action(self.environ.get_curr_state()) # choose_action returns a dictionary
        else:
            chess_move = self.B_rl_agent.choose_action(self.environ.get_curr_state()) # choose_action returns a dictionary
        
        if self.environ.load_chessboard(chess_move['chess_move_str']):
            self.environ.update_curr_state()
            
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Chessboard was successfully loaded with move: {chess_move}\n')
                print_statements_debug.write(f'Chessboard looks like this:\n\n')
                print_statements_debug.write(f'\n {self.environ.board}\n\n')
                print_statements_debug.write(f'Current turn is: {self.environ.get_curr_turn()}\n')
                print_statements_debug.write(f'Current turn index is: {self.environ.turn_index}\n')
                print_statements_debug.write("Bye from Bradley.rl_agent_selects_chess_move\n\n\n")

            return chess_move
        else:
            error_log.write(f'Error: failed to load chessboard with move: {chess_move}\n')
            error_log.write("========== Bye from Bradley.rl_agent_selects_chess_move ==========\n\n\n")
            return {'chess_move_str': 'invalid chess move or something went wrong'}
    ### end of rl_agent_selects_chess_move
    
    def get_fen_str(self) -> str:
        """Returns the FEN string representing the current board state.
        Call this method at each point in the chess game to get the FEN string representing the current board state.
        The FEN string can be used to reconstruct a chessboard position.

        Args:
            None
        Returns:
            str: A string representing the current board state in FEN format, 
            such as 'rnbqkbnr/pppp1ppp/8/8/4p1P1/5P2/PPPPP2P/RNBQKBNR w KQkq - 0 3'.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_fen_str ==========\n\n")

        try:
            fen: str = self.environ.board.fen()
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'FEN string is: {fen}\n')
                print_statements_debug.write("Bye from Bradley.get_fen_str\n\n\n")
            return fen
        except Exception as e:
            error_log.write(f'An error occurred: {e}\n')
            error_log.write("========== Bye from Bradley.get_fen_str ==========\n\n\n")
            return 'invalid board state, no fen str'
    ### end of get_gen_str ###

    def get_opp_agent_color(self, rl_agent_color: str) -> str:
        """Determines the color of the opposing RL agent.
        Call this method to determine the color of the opposing RL agent, given the color of the current RL agent.

        Args:
            rl_agent_color (str): A string indicating the color of the current RL agent, either 'W' or 'B'.
        Returns:
            str: A string indicating the color of the opposing RL agent, either 'W' or 'B'.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_opp_agent_color ==========\n\n")

        if rl_agent_color == 'W':
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Opposing agent color is: B\n')
                print_statements_debug.write("Bye from Bradley.get_opp_agent_color\n\n\n")
            return 'B'
        else:
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Opposing agent color is: W\n')
                print_statements_debug.write("Bye from Bradley.get_opp_agent_color\n\n\n")
            return 'W'
    ### end of get_opp_agent_color
            
    # @log_config.log_execution_time_every_N()        
    def get_curr_turn(self) -> str:
        """Returns the current turn as a string.
        Call this method to get the current turn as a string, such as 'W1' or 'B5'.

        Args:
            None
        Returns:
            str: A string representing the current turn.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_curr_turn ==========\n\n")
        
        curr_turn = self.environ.get_curr_turn()

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Current turn is: {curr_turn}\n')
            print_statements_debug.write("Bye from Bradley.get_curr_turn\n\n\n")

        return curr_turn
    ### end of get_curr_turn

    # @log_config.log_execution_time_every_N()
    def game_on(self) -> bool:
        """Determines whether the game is still ongoing.
        Call this method to determine whether the game is still ongoing. The game can end if the Python chess board determines the game is over,
        or if the game is at `max_num_turns_per_player * 2 - 1` moves per player (minus 1 because the index starts at 0).

        Args:
            None
        Returns:
            bool: A boolean value indicating whether the game is still ongoing (`True`) or not (`False`).
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.game_on ==========\n\n")

        if self.environ.board.is_game_over() or self.environ.turn_index >= self.settings.max_num_turns_per_player * 2 - 1:
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Game over, game_on is: False\n')
                print_statements_debug.write("Bye from Bradley.game_on\n\n\n")
            return False
        else:
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Game is still ongoing, game_on is: True\n')
                print_statements_debug.write("========== Bye from Bradley.game_on ==========\n\n\n")
            return True
    ### end of game_on

    # @log_config.log_execution_time_every_N()
    def get_legal_moves(self) -> list[str]:
        """Returns a list of legal moves for the current turn and state of the chessboard.
        Call this method to get a list of legal moves for the current turn and state of the chessboard.

        Args:
            None
        Returns:
            list[str]: A list of strings representing the legal moves for the current turn and state of the chessboard.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_legal_moves ==========\n\n")

        legal_moves = self.environ.get_legal_moves()

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Legal moves are: {legal_moves}\n')
            print_statements_debug.write("========== Bye from Bradley.get_legal_moves ===========\n\n\n")

        return legal_moves
    ### end of get_legal_moves
    
    def get_rl_agent_color(self) -> str: 
        """Returns the color of the RL agent.
        Call this method to get the color of the RL agent.

        Args:
            None
        Returns:
            str: A string indicating the color of the RL agent, either 'W' or 'B'.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_rl_agent_color ==========\n\n")
            print_statements_debug.write(f'RL agent color is: {self.rl_agent.color}\n')
            print_statements_debug.write("========== Bye from Bradley.get_rl_agent_color ===========\n\n\n")

        return self.rl_agent.color
    ### end of get_rl_agent_color
    
    # @log_config.log_execution_time_every_N()
    def get_game_outcome(self) -> chess.Outcome or str:   
        """ Returns the outcome of the chess game.
        Call this method to get the outcome of the chess game, either '1-0', '0-1', '1/2-1/2', 
        or 'False' if the outcome is not available.

        Args:
            None
        Returns:
            chess.Outcome or str: An instance of the `chess.Outcome` class with a `result()` 
            method that returns the outcome of the game, or a string indicating that the outcome is not available.
        Raises:
        AttributeError: If the outcome is not available due to an invalid board state.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_game_outcome ==========\n\n")

        try:
            game_outcome = self.environ.board.outcome().result()
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Game outcome is: {game_outcome}\n')
                print_statements_debug.write("========== Bye from Bradley.get_game_outcome ===========\n\n\n")

            return game_outcome
        except AttributeError as e:
            error_log.write(f'An error occurred: {e}\n')
            error_log.write("========== Bye from Bradley.get_game_outcome ===========\n\n\n")
            return 'outcome not available, most likely game ended because turn_index was too high or player resigned'
    ### end of get_game_outcome
    
    # @log_config.log_execution_time_every_N()
    def get_game_termination_reason(self) -> str:
        """Determines why the game ended.
        Call this method to determine why the game ended. If the game ended due to a checkmate, 
        a string 'termination.CHECKMATE' will be returned. This method will raise an `AttributeError` 
        exception if the outcome is not available due to an invalid board state.

        Args:
            None
        Returns:
            str: A single string that describes the reason for the game ending.
        Raises:
            AttributeError: If the outcome is not available due to an invalid board state.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_game_termination_reason ==========\n\n")

        try:
            termination_reason = str(self.environ.board.outcome().termination)

            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Termination reason is: {termination_reason}\n')
                print_statements_debug.write("========== Bye from Bradley.get_game_termination_reason ===========\n\n\n")

            return termination_reason
        except AttributeError as e:
            error_log.write(f'An error occurred: {e}\n')
            error_log.write("========== Bye from Bradley.get_game_termination_reason ===========\n\n\n")
            return 'termination reason not available, most likely game ended because turn_index was too high or player resigned'
    ### end of get_game_termination_reason
    
    def get_chessboard(self) -> chess.Board:
        """Returns the current state of the chessboard.
        Call this method to get the current state of the chessboard as a `chess.Board` object. The `chess.Board` 
        object can be printed to get an ASCII representation of the chessboard and current state of the game.

        Args:
            None
        Returns:
            chess.Board: A `chess.Board` object representing the current state of the chessboard.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_chessboard ==========\n\n")
            print_statements_debug.write(f'Chessboard looks like this:\n\n')
            print_statements_debug.write(f'\n {self.environ.board}\n\n')
            print_statements_debug.write("========== Bye from Bradley.get_chessboard ===========\n\n\n")

        return self.environ.board
    ### end of get_chess_board

    # @log_config.log_execution_time_every_N()
    def train_rl_agents(self, training_results_filepath: str) -> None:
        """Trains the RL agents using the SARSA algorithm and sets their `is_trained` flag to True.
        The algorithm used for training is SARSA. Two rl agents train each other
        A chess game can end at multiple places during training, so we need to 
        check for end-game conditions throughout this method.

        The agents are trained by playing games from a database exactly as
        shown, and learning from that. Then the agents are trained again (in another method), 
        but this time they makes their own decisions. A White or Black agent can be trained.

        This training regimen first trains the agents to play a good positional game.
        Then when the agents are retrained, the agents behaviour can be fine-tuned
        by adjusting hyperparameters.

        Args:
            training_results_filepath (str): The file path to save the training results to.
        Returns: 
                None
        """ 

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.train_rl_agents ==========\n\n")

        training_results = open(training_results_filepath, 'a')
        PRINT_RESULTS: bool = True

        W_curr_Qval: int = self.settings.initial_q_val
        B_curr_Qval: int = self.settings.initial_q_val

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'White agent initial Q value is: {W_curr_Qval}\n')
            print_statements_debug.write(f'Black agent initial Q value is: {B_curr_Qval}\n')

        # for each game in the training data set. game_num_str, this looks like 'W10'
        for game_num_str in self.chess_data.index:
            num_chess_moves_curr_training_game: int = self.chess_data.at[game_num_str, 'Num Moves']
            
            if PRINT_RESULTS:
                training_results.write(f'\n\n Start of {game_num_str} training\n\n')
                training_results.write(f'Number of chess moves in this game is: {num_chess_moves_curr_training_game}\n')

            # initialize environment to provide a state, s
            curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Current state is: {curr_state}\n')

            # loop plays through one game in the database, exactly as shown.
            while curr_state['turn_index'] < num_chess_moves_curr_training_game:
                ##################### WHITE'S TURN ####################
                ##### WHITE AGENT PICKS MOVE, DONT PLAY IT YET THOUGH!!! #####
                # choose action a from state s, using policy
                W_chess_move = self.rl_agent_PICKS_move_training_mode(curr_state, self.W_rl_agent.color, game_num_str)

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'White agent picked move: {W_chess_move}\n')
                    print_statements_debug.write(f'on turn: {curr_state["turn_index"]}\n')

                ##### ASSIGN POINTS TO Q_TABLE FOR WHITE #####
                # on the first turn for white, this would assign to W1 col at chess_move row.
                # on W's second turn, this would be Q_next which is calculated on the first loop.
                curr_turn: str = curr_state['curr_turn']
                self.assign_points_to_Q_table_training_mode(W_chess_move, curr_turn, W_curr_Qval, self.W_rl_agent.color)
                
                ##### WHITE AGENT PLAYS SELECTED MOVE, and GET REWARD FOR THAT MOVE #####
                # take action a, observe r, s', and load chessboard
                W_reward = self.rl_agent_PLAYS_move_training_mode(W_chess_move)

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'White agent played move: {W_chess_move}\n')
                    print_statements_debug.write(f'White agent got reward: {W_reward}\n')
                
                # the state changes each time a move is made, so get curr state again.    
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()
                
                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'Current state is: {curr_state}\n')

                ##### FIND THE ESTIMATED Q VALUE FOR WHITE #####
                # check for game end condition
                if curr_state['turn_index'] >= num_chess_moves_curr_training_game:
                    if PRINT_RESULTS_DEBUG:
                        print_statements_debug.write(f'Game ended on White turn\n')
                        print_statements_debug.write(f'curr_state["turn_index"] is: {curr_state["turn_index"]}\n')
                        print_statements_debug.write(f'num_chess_moves_curr_training_game is: {num_chess_moves_curr_training_game}\n')
                    break
                else:
                    W_est_Qval: int = self.find_estimated_Q_value()
                    if PRINT_RESULTS_DEBUG:
                        print_statements_debug.write(f'Estimated Q value for White is: {W_est_Qval}\n')

                ##################### BLACK'S TURN ####################
                ##### BLACK AGENT PICKS MOVE, DONT PLAY IT YET THOUGH!!! #####
                B_chess_move = self.rl_agent_PICKS_move_training_mode(curr_state, self.B_rl_agent.color, game_num_str)

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f"Black chess move is: {B_chess_move}\n")
                
                ##### ASSIGN POINTS TO Q_TABLE FOR BLACK #####
                curr_turn: str = curr_state['curr_turn']
                self.assign_points_to_Q_table_training_mode(B_chess_move, curr_turn, B_curr_Qval, self.B_rl_agent.color)

                ##### BLACK AGENT PLAYS SELECTED MOVE and GET REWARD FOR THAT MOVE #####
                # take action a, observe r, s', and load chessboard
                B_reward = self.rl_agent_PLAYS_move_training_mode(B_chess_move)

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'B reward is: {B_reward} for playing move: {B_chess_move}\n')

                # the state changes each time a move is made, so get curr state again.                
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'Current state is: {curr_state}\n')

                if self.environ.turn_index >= self.settings.max_num_turns_per_player * 2:
                    # index has reached max value, this will only happen for Black at Black's final max turn, 
                    # White won't ever have this problem.

                    if PRINT_RESULTS_DEBUG:
                        print_statements_debug.write(
                            f"game is over, max number of turns has been reached: "
                            f"{self.environ.turn_index} >= {self.settings.max_num_turns_per_player}\n")
                    break

                ##### FIND THE ESTIMATED Q VALUE FOR BLACK #####
                # check for game end condition
                if curr_state['turn_index'] >= num_chess_moves_curr_training_game:
                    if PRINT_RESULTS_DEBUG:
                        print_statements_debug.write(f'Game ended on Blacks turn\n')
                        print_statements_debug.write(f'curr_state["turn_index"] is: {curr_state["turn_index"]}\n')
                        print_statements_debug.write(f'num_chess_moves_curr_training_game is: {num_chess_moves_curr_training_game}\n')
                    break
                else:
                    B_est_Qval: int = self.find_estimated_Q_value()

                    if PRINT_RESULTS_DEBUG:
                        print_statements_debug.write(f'estimated b q val is: {B_est_Qval}\n')

                # ***CRITICAL STEP***, this is the main part of the SARSA algorithm. 
                W_next_Qval: int = self.find_next_Qval(W_curr_Qval, self.W_rl_agent.settings.learn_rate, W_reward, self.W_rl_agent.settings.discount_factor, W_est_Qval)
                B_next_Qval: int = self.find_next_Qval(B_curr_Qval, self.B_rl_agent.settings.learn_rate, B_reward, self.B_rl_agent.settings.discount_factor, B_est_Qval)

                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write("SARSA calc was successful\n")
                    print_statements_debug.write(f'W next Q val is: {W_next_Qval}\n')
                    print_statements_debug.write(f'B next Q val is: {B_next_Qval}\n')
            
                # on the next turn, this Q value will be added to the Q table. so if this is the end of the first round,
                # next round it will be W2 and then we assign the q value at W2 col
                W_curr_Qval = W_next_Qval
                B_curr_Qval = B_next_Qval

                # this is the next state, s'  the next action, a' is handled at the beginning of the while loop
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()
                
                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'Current state is: {curr_state}\n')
            # end curr game while loop

            # this curr game is done, reset environ to prepare for the next game
            if PRINT_RESULTS:
                training_results.write(f'Game {game_num_str} is over.\n')
                training_results.write(f'\nThe Chessboard looks like this:\n')
                training_results.write(f'\n {self.environ.board}\n\n')
                training_results.write(f'Game result is: {self.get_game_outcome()}\n')
                training_results.write(f'The game ended because of: {self.get_game_termination_reason()}\n')
            
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Game {game_num_str} is over.\n')
                print_statements_debug.write(f'\nThe Chessboard looks like this:\n')
                print_statements_debug.write(f'\n {self.environ.board}\n\n')
                print_statements_debug.write(f'Game result is: {self.get_game_outcome()}\n')
                print_statements_debug.write(f'The game ended because of: {self.get_game_termination_reason()}\n')

            self.reset_environ()
        # end of training, all games in database have been processed
        
        # training is complete
        self.W_rl_agent.is_trained = True
        self.B_rl_agent.is_trained = True
        training_results.close()
        self.reset_environ()

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'White agent is trained: {self.W_rl_agent.is_trained}\n')
            print_statements_debug.write(f'Black agent is trained: {self.B_rl_agent.is_trained}\n')
            print_statements_debug.write("========== Bye from Bradley.train_rl_agents ===========\n\n\n")
    ### end of train_rl_agents

    # @log_config.log_execution_time_every_N()
    def continue_training_rl_agents(self, training_results_filepath: str, num_games_to_play: int) -> None:
        """ continues to train the agent, this time the agents make their own decisions instead 
            of playing through the database.
        """ 
        training_results = open(training_results_filepath, 'a')
        PRINT_RESULTS: bool = True

        W_curr_Qval: int = self.settings.initial_q_val
        B_curr_Qval: int = self.settings.initial_q_val

        for curr_training_game in range(num_games_to_play):
            if PRINT_RESULTS:
                training_results.write(f'\n\n Start of game {curr_training_game} training\n\n') 
            
            curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

            while self.game_on():
                #################### WHITE'S TURN ####################
                ##### WHITE AGENT PICKS MOVE, DONT PLAY IT YET THOUGH #####
                W_chess_move = self.rl_agent_PICKS_move_training_mode(curr_state, self.W_rl_agent.color)

                ##### ASSIGN POINTS TO Q_TABLE FOR WHITE #####
                curr_turn: str = curr_state['curr_turn']
                self.assign_points_to_Q_table_training_mode(W_chess_move, curr_turn, W_curr_Qval, self.W_rl_agent.color)

                ##### WHITE AGENT PLAYS SELECTED MOVE and GET REWARD FOR THAT MOVE #####
                W_reward = self.rl_agent_PLAYS_move_training_mode(W_chess_move)

                # the state changes each time a move is made, so get curr state again.
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

                ##### FIND THE ESTIMATED Q VALUE FOR WHITE #####
                if not self.game_on():
                    break
                else:
                    W_est_Qval: int = self.find_estimated_Q_value()

                #################### BLACK'S TURN ####################
                ##### BLACK AGENT PICKS MOVE, DONT PLAY IT YET THOUGH #####
                B_chess_move = self.rl_agent_PICKS_move_training_mode(curr_state, self.B_rl_agent.color)

                ##### ASSIGN POINTS TO Q_TABLE FOR BLACK #####
                curr_turn: str = curr_state['curr_turn']
                self.assign_points_to_Q_table_training_mode(B_chess_move, curr_turn, B_curr_Qval, self.B_rl_agent.color)

                ##### BLACK AGENT PLAYS SELECTED MOVE and GET REWARD FOR THAT MOVE #####
                B_reward = self.rl_agent_PLAYS_move_training_mode(B_chess_move)

                # the state changes each time a move is made, so get curr state again.
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

                if self.environ.turn_index >= self.settings.max_num_turns_per_player * 2:
                    # index has reached max value, this will only happen for Black at Black's final max turn, 
                    # White won't ever have this problem.
                    break

                ##### FIND THE ESTIMATED Q VALUE FOR BLACK #####
                if not self.game_on():
                    break
                else:
                    B_est_Qval: int = self.find_estimated_Q_value()

                # *** CRITICAL STEP ***, this is the main part of the SARSA algorithm.
                W_next_Qval: int = self.find_next_Qval(W_curr_Qval, self.W_rl_agent.settings.learn_rate, W_reward, self.W_rl_agent.settings.discount_factor, W_est_Qval)
                B_next_Qval: int = self.find_next_Qval(B_curr_Qval, self.B_rl_agent.settings.learn_rate, B_reward, self.B_rl_agent.settings.discount_factor, B_est_Qval)
                
                W_curr_Qval = W_next_Qval
                B_curr_Qval = B_next_Qval

                # this is the next state, s'  the next action, a' is handled at the beginning of the while loop
                curr_state: dict[str, str, list[str]] = self.environ.get_curr_state()

            # reset environ to prepare for the next game
            training_results.write(f'Game {curr_training_game} is over.\n')
            training_results.write(f'\nChessboard looks like this:\n\n')
            training_results.write(f'\n {self.environ.board}\n\n')
            training_results.write(f'Game result is: {self.get_game_outcome()}\n')
            training_results.write(f'The game ended because of: {self.get_game_termination_reason()}\n')
            self.reset_environ()
        
        training_results.close()   
        self.reset_environ()
    ### end of continue_training_rl_agents

    ########## TRAINING HELPER METHODS ####################
    
    # @log_config.log_execution_time_every_N()
    def rl_agent_PICKS_move_training_mode(self, curr_state: dict[str, str, list[str]], rl_agent_color: str, game_num_str: str = 'Game 1') -> str:
        """
        This method is used by the RL agent to pick a move during training mode. 
        It takes in the current state of the chessboard,
        the color of the RL agent, and the game number as input parameters. 
        It returns the chess move as a string that the RL agent
        has chosen to play.

        Parameters:
            curr_state (dict[str, str, list[str]]): A dictionary containing the current state of the chessboard.
            rl_agent_color (str): A string representing the color of the RL agent ('W' for white, 'B' for black).
            game_num_str (str): A string representing the game number (default is 'Game 1').
        Returns:
            str: A string representing the chess move that the RL agent has chosen to play.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.rl_agent_PICKS_move_training_mode ==========\n\n")

        if rl_agent_color == 'W':
            curr_action: dict[str] = self.W_rl_agent.choose_action(curr_state, game_num_str)
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'White agent picked move: {curr_action["chess_move_str"]}\n')
        else:
            curr_action: dict[str] = self.B_rl_agent.choose_action(curr_state, game_num_str)
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Black agent picked move: {curr_action["chess_move_str"]}\n')
        
        chess_move: str = curr_action['chess_move_str']

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write("========== Bye from Bradley.rl_agent_PICKS_move_training_mode ===========\n\n\n")

        return chess_move
    # end of rl_agent_picks_move_training_mode
    
    # @log_config.log_execution_time_every_N()
    def assign_points_to_Q_table_training_mode(self, chess_move: str, curr_turn: str, curr_Qval: int, rl_agent_color: str) -> None:
        """ Assigns points to the Q table for the given chess move, current turn, current Q value, and RL agent color.
        Args:
            chess_move (str): The chess move to assign points to in the Q table.
            curr_turn (str): The current turn of the game.
            curr_Qval (int): The current Q value for the given chess move.
            rl_agent_color (str): The color of the RL agent making the move.
        Returns:
            None
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.assign_points_to_Q_table_training_mode ==========\n\n")
            print_statements_debug.write(f'Chess move is: {chess_move}\n')
            print_statements_debug.write(f'Current turn is: {curr_turn}\n')
            print_statements_debug.write(f'Current Q value is: {curr_Qval}\n')
            print_statements_debug.write(f'RL agent color is: {rl_agent_color}\n')

        if rl_agent_color == 'W':
            try:
                self.W_rl_agent.change_Q_table_pts(chess_move, curr_turn, curr_Qval)
            except KeyError: 
                # chess move is not represented in the Q table, update Q table and try again.
                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'Chess move is not represented in the White Q table, updating Q table and trying again...\n')

                self.W_rl_agent.update_Q_table([chess_move])
                self.W_rl_agent.change_Q_table_pts(chess_move, curr_turn, curr_Qval)
        else:
            try:
                self.B_rl_agent.change_Q_table_pts(chess_move, curr_turn, curr_Qval)
            except KeyError: 
                # chess move is not represented in the Q table, update Q table and try again.
                if PRINT_RESULTS_DEBUG:
                    print_statements_debug.write(f'Chess move is not represented in the Black Q table, updating Q table and trying again...\n')

                self.B_rl_agent.update_Q_table([chess_move])
                self.B_rl_agent.change_Q_table_pts(chess_move, curr_turn, curr_Qval)
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write("========== Bye from Bradley.assign_points_to_Q_table_training_mode ===========\n\n\n")
    # enf of assign_points_to_Q_table_training_mode

    # @log_config.log_execution_time_every_N()
    def rl_agent_PLAYS_move_training_mode(self, chess_move: str) -> int:
        """ Simulates the RL agent playing a given chess move in training mode and returns the reward for that move.
        This method is responsible for:
            1. Loading the chessboard with the given move.
            2. Updating the current state of the environment.
            3. Analyzing the board state to determine the reward for the current move.
    
        The reward is determined based on the analysis of the board state. If there's no impending checkmate, 
        the reward is the centipawn score of the board state. Otherwise, the reward is computed based on the 
        impending checkmate turns multiplied by a predefined mate score reward.
    
        Args:
            chess_move (str): A string representing the chess move in standard algebraic notation.
        Returns:
            int: The reward for the given chess move.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.rl_agent_PLAYS_move_training_mode ==========\n\n")
            print_statements_debug.write(f'Chess move is: {chess_move}\n')

        self.environ.load_chessboard(chess_move)
        self.environ.update_curr_state()

        # analyze board to get reward for curr move
        # false means we don't care about the anticipated next move yet (we do care later in the training)
        analysis_results = self.analyze_board_state(self.get_chessboard(), False)
    
        if analysis_results['mate_score'] is None:
            reward = analysis_results['centipawn_score']
        else: # there is an impending checkmate
            reward = analysis_results['mate_score'] * self.settings.mate_score_reward
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Reward for move is: {reward}\n')
            print_statements_debug.write("========== Bye from Bradley.rl_agent_PLAYS_move_training_mode ===========\n\n\n")

        return reward
    # end of rl_agent_PLAYS_move_training_mode

    # @log_config.log_execution_time_every_N()
    def find_estimated_Q_value(self) -> int:
        """ Estimates the Q-value for the RL agent's next action without actually playing the move.
        This method simulates the agent's next action and the anticipated response from the opposing agent 
        to estimate the Q-value. The method:
        1. Observes the next state of the chessboard after the agent's move.
        2. Analyzes the current state of the board to predict the opposing agent's response.
        3. Loads the board with the anticipated move of the opposing agent.
        4. Estimates the Q-value based on the anticipated state of the board.
    
        The estimation of the Q-value is derived from analyzing the board state with the help of a chess engine 
        (like Stockfish). If there's no impending checkmate, the estimated Q-value is the centipawn score of 
        the board state. Otherwise, it's computed based on the impending checkmate turns multiplied by a predefined 
        mate score reward.

        After estimating the Q-value, the method reverts the board state to its original state before the simulation.
        
        Args:
            None            
        Returns:
            int: The estimated Q-value for the agent's next action.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.find_estimated_Q_value ==========\n\n")

        ##### RL AGENT CHOOSES NEXT ACTION, BUT DOES NOT PLAY IT !!! #####
        # observe next_state, s' (this would be after the player picks a move
        # and choose action a'

        # RL agent just played a move. the board has changed, if stockfish analyzes the board, 
        # it will give points for the agent, based on the agent's latest move.
        # We also need the points for the ANTICIPATED next state, 
        # given the ACTICIPATED next action. In this case, the anticipated response from opposing agent.

        # analysis returns an array of dicts. in our analysis, we only consider the first dict returned by 
        # the stockfish analysis. We also care about the opponents likely chess move in response to our own.                    
        analysis_results = self.analyze_board_state(self.get_chessboard())
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Analysis results are: {analysis_results}\n')

        #load up the chess board with Black's anticipated chess move               
        self.environ.load_chessboard_for_Q_est(analysis_results) # anticipated next action is a str like, 'e6f2'
    
        # this is the Q estimated value due to what the opposing agent is likely to play in response to our move.
        # we want the points, but NOT the anticipated next move. confusing, I KNOW, but it's 100% correct, just trust me.
        est_Qval_analysis = self.analyze_board_state(self.get_chessboard(), False) 
    
        # get pts for est_Qval 
        if est_Qval_analysis['mate_score'] is None:
            est_Qval = est_Qval_analysis['centipawn_score']
        else: # there is an impending checkmate
            est_Qval = est_Qval_analysis['mate_score'] * self.settings.mate_score_reward

        # IMPORTANT STEP!!! pop the chessboard of last move, we are estimating board states, not
        # playing a move.
        self.environ.pop_chessboard()
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'estimated q val is: {est_Qval}\n')
            print_statements_debug.write("========== Bye from Bradley.find_estimated_Q_value ===========\n\n\n")

        return est_Qval
    # end of find_estimated_Q_value

    # @log_config.log_execution_time_every_N()
    def find_next_Qval(self, curr_Qval: int, learn_rate: float, reward: int, discount_factor: float, est_Qval: int) -> int:
        """
        Calculates the next Q-value based on the current Q-value, learning rate, reward, discount factor, and estimated Q-value.
        This method uses the Q-learning update formula to compute the next Q-value. 

        The formula ensures that the agent incorporates the current reward and the highest Q-value of the next state 
        into the current Q-value, balanced by the learning rate.
    
        Args:
            curr_Qval (int): The current Q-value.
            learn_rate (float): The learning rate, a value between 0 and 1.
            reward (int): The reward obtained from the current action.
            discount_factor (float): The discount factor to consider future rewards, a value between 0 and 1.
            est_Qval (int): The estimated Q-value for the next state-action pair.
        Returns:
            int: The updated or next Q-value.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.find_next_Qval ==========\n\n")
            print_statements_debug.write(f'Current Q value is: {curr_Qval}\n')
            print_statements_debug.write(f'Learning rate is: {learn_rate}\n')
            print_statements_debug.write(f'Reward is: {reward}\n')
            print_statements_debug.write(f'Discount factor is: {discount_factor}\n')
            print_statements_debug.write(f'Estimated Q value is: {est_Qval}\n')

        next_Qval = curr_Qval + learn_rate * (reward + ((discount_factor * est_Qval) - curr_Qval))

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Next Q value is: {next_Qval}\n')
            print_statements_debug.write("========== Bye from Bradley.find_next_Qval ===========\n\n\n")
        return next_Qval
    # end of find_next_Qval
    
    ########## END OF TRAINING HELPER METHODS ####################

    # @log_config.log_execution_time_every_N()
    def analyze_board_state(self, board: chess.Board, is_for_est_Qval_analysis: bool = True) -> dict:
        """Analyzes the current state of the chessboard using the Stockfish engine.
        This method analyzes the current state of the chessboard using the Stockfish engine and returns a dictionary with the analysis results. The analysis results include the mate score and centipawn score, which are normalized by looking at the board from White's perspective. If `is_for_est_Qval_analysis` is True, the anticipated next move from the opposing agent is also included in the analysis results.

        Args:
            board (chess.Board): The current state of the chessboard to analyze.
            is_for_est_Qval_analysis (bool): A boolean indicating whether the analysis is for estimating the Q-value during training. Defaults to True.
        Returns:
            dict: A dictionary with the analysis results, including the mate score and centipawn score. 
            If `is_for_est_Qval_analysis` is True, the anticipated next move from the opposing agent is also included in the analysis results.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.analyze_board_state ==========\n\n")
            print_statements_debug.write(f'Board is: {board}\n')
            print_statements_debug.write(f'is_for_est_Qval_analysis is: {is_for_est_Qval_analysis}\n')

        # analysis_result is an InfoDict (see python-chess documentation)
        analysis_result = self.engine.analyse(board, self.settings.search_limit, multipv = self.settings.num_moves_to_return)
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Analysis result is: {analysis_result}\n')

        # normalize by looking at it from White's perspective
        # score datatype is Cp (centipawn) or Mate
        score = analysis_result[0]['score'].white()
        mate_score = score.mate()
        centipawn_score = score.score()

        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Normalized mate score is: {mate_score}\n')
            print_statements_debug.write(f'Normalized centipawn score is: {centipawn_score}\n')

        if is_for_est_Qval_analysis:
            anticipated_next_move = analysis_result[0]['pv'][0] # this would be the anticipated response from opposing agent
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write(f'Anticipated next move is: {anticipated_next_move}\n')
                print_statements_debug.write("========== Bye from Bradley.analyze_board_state ===========\n\n\n")
            
            return {'mate_score': mate_score, 'centipawn_score': centipawn_score, 'anticipated_next_move': anticipated_next_move}
        else:
            # we don't need the anticipated next move because we just want the points for our move.
            if PRINT_RESULTS_DEBUG:
                print_statements_debug.write("========== Bye from Bradley.analyze_board_state ===========\n\n\n")
            
            return {'mate_score': mate_score, 'centipawn_score': centipawn_score} 
    ### end of analyze_board_state
 
    # @log_config.log_execution_time_every_N()
    def get_reward(self, chess_move_str: str) -> int:                                     
        """Calculates the reward for a given chess move.
        This method calculates the reward for a given chess move based on the type of move. The reward is returned as an integer.

        Args:
            chess_move_str (str): A string representing the selected chess move.
        Returns:
            int: The reward based on the type of move as an integer.
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.get_reward ==========\n\n")
            print_statements_debug.write(f'Chess move is: {chess_move_str}\n')

        total_reward = 0
        if re.search(r'N.', chess_move_str): # encourage development of pieces
            total_reward += self.settings.piece_dev_pts
        if re.search(r'R.', chess_move_str):
            total_reward += self.settings.piece_dev_pts
        if re.search(r'B.', chess_move_str):
            total_reward += self.settings.piece_dev_pts
        if re.search(r'Q.', chess_move_str):
            total_reward += self.settings.piece_dev_pts
        if re.search(r'x', chess_move_str):    # capture
            total_reward += self.settings.capture_pts
        if re.search(r'=Q', chess_move_str):    # a promotion to Q
            total_reward += self.settings.promotion_Queen_pts
        if re.search(r'#', chess_move_str): # checkmate
            total_reward += self.settings.checkmate_pts
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f'Total reward is: {total_reward}\n')
            print_statements_debug.write("========== Bye from Bradley.get_reward ===========\n\n\n")

        return total_reward
    ## end of get_reward

    # @log_config.log_execution_time_every_N()
    def reset_environ(self) -> None:
        """Resets the environment for a new game.
        This method is useful when training and also when finding the value of each move. The board needs to be cleared each time a game is played.

        Args:
            None
        Returns:
            None
        """
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write(f"========== Hello from Bradley.reset_environ ==========\n\n")
        
        self.environ.reset_environ()
        
        if PRINT_RESULTS_DEBUG:
            print_statements_debug.write("Environment has been reset\n")
            print_statements_debug.write("========== Bye from Bradley.reset_environ ===========\n\n\n")
    ### end of reset_environ