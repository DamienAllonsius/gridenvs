import unittest
from gridenvs.utils import Point
from q.q import Q
from option.option import Option
from agent.agent import AgentOption

class QTests(unittest.TestCase):
    """
    TODO : test_update_q_dict
    TODO : redo the tests, replace 'action' by 'Point(x,y)' (add_action_to_state has to evaluate the action)
    """
    def test_add_state(self):
        q = Q(Point(0,0))
        exists_state = q.add_state(Point(0,1))
        self.assertFalse(exists_state)
        self.assertEqual(q.q_dict, {Point(0,0).__hash__() : {}, Point(0,1).__hash__() : {}})

    def test_add_action_to_state(self):
        q = Q(Point(0,0))
        known_action = q.add_action_to_state(Point(0,0), Point(2,2))
        self.assertEqual(q.q_dict, {Point(0,0).__hash__() : {Point(2,2).__hash__() : 0}})
        self.assertFalse(known_action)

        #with  self.assertRaises(KeyError):
        #    known_second_action = q.add_action_to_state(Point(0,3), Point(0,1))
            
        known_third_action = q.add_action_to_state(Point(0,0), Point(4,4))
        self.assertFalse(known_third_action)
        self.assertEqual(q.q_dict, {Point(0,0).__hash__() : {Point(2,2).__hash__() : 0, Point(4,4).__hash__() : 0}})

    def test_add_action_to_state_with_option(self):
        position_1 = Point(0,0)
        zone_1 = Point(0,0)
        terminal_zone = Point(1,0)
        option_1 = Option(zone = zone_1, position = position_1, terminal_state = terminal_zone)
        option_2 = Option(zone = zone_1, position = position_1, terminal_state = terminal_zone)
        self.assertTrue(option_1 == option_2)
        
    def test_find_best_action(self):
        q = Q(Point(0,0))
        q.add_action_to_state(Point(0,0), Point(0,0))
        q.q_dict[Point(0,0).__hash__()][Point(0,0).__hash__()] = 2
        q.add_action_to_state(Point(0,0), Point(0,1))
        q.q_dict[Point(0,0).__hash__()][Point(0,1).__hash__()] = 4
        q.add_action_to_state(Point(0,0), Point(0,2))
        q.q_dict[Point(0,0).__hash__()][Point(0,2).__hash__()] = 77
        q.add_action_to_state(Point(0,0), Point(0,3))
        q.q_dict[Point(0,0).__hash__()][Point(0,3).__hash__()] = 3
        q.add_state(Point(10,10))

        best_reward, best_action = q.find_best_action(Point(0,0))
        self.assertEqual(best_reward, 77)
        self.assertEqual(best_action, Point(0,2))
        with self.assertRaises(Exception):
            q.find_best_action(Point(10,10))        
        with self.assertRaises(Exception):
            q.find_best_action(Point(4,4))

    def test_find_best_action_with_options(self):
        
        q = Q(Point(0,0))
        agent = AgentOption(Point(0,0),Point(0,0))
        q.add_action_to_state(Point(0,0), agent.explore_option)
        q.q_dict[Point(0,0).__hash__()][agent.explore_option.__hash__()] = 2

        best_reward, best_action = q.find_best_action(Point(0,0))
        self.assertEqual(best_reward, 2)
        self.assertEqual(best_action, agent.explore_option)

        opt = Option(Point(0,0), Point(0,1), terminal_state = (2,2))
        q.add_state(Point(0,1))
        q.add_action_to_state(Point(0,1), opt)
        self.assertEqual(0, q.q_dict[Point(0,1).__hash__()][opt.__hash__()])

        opt_2 = Option(Point(0,0), Point(1,1), terminal_state = (2,2))
        bool = q.add_action_to_state(Point(0,1), opt)
        self.assertTrue(bool)

    def test_is_actions(self):
        q = Q(Point(0,0))
        q.add_action_to_state(Point(0,0), Point(2,2))
        q.add_state(Point(1,1))
        self.assertTrue(q.is_actions(Point(0,0)))
        self.assertFalse(q.is_actions(Point(1,1)))
        """
    def test_update_q_dict(self):
        state = 'state' 
        new_state = 'new_state'
        action = 'action' 
        reward = 10
        t = 5
        q = Q(state)
        q.add_action_to_state(state, action)
        q.update_q_dict(state, new_state, action, reward, t)
        assertEqual(q.q_dict, {'state' : {}, 'new_state' : {}})
        """
if __name__ == '__main__':
    unittest.main()
