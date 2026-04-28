/* VGroup PML model */
/* This model verifies 4 properties of the infrastructure of the traffic system */
/* Properties: */
/* 1. At every intersection, every vehicle eventually gets its turn of green signal. */
/* 2. At every intersection, the green signal is granted unconditionally fairly among all directions. */
/* 3. At any moment at any intersection, there is only one light is green. */
/* 4. At every intersection, once the green is set, it stays green for at minimum green time units (10). */

/* Abstract intersections from coordinates to IDs */

#define I1 0
#define I2 1
#define I3 2
#define I4 3
#define I5 4
#define I6 5
#define I7 6
#define I8 7
#define I9 8

/* Define at direction from python code */
#define STOP 0
#define UP 1
#define RIGHT 2
#define DOWN 3
#define LEFT 4

/* Define the light status from python code */
#define GREEN 0
#define RED 1

/* Define number for not set or no value */
#define NONE 255

/* Define number of vehicles and intersections in this model */
#define NUM_VEHICLES 3
#define NUM_INTERSECTIONS 9

/* Define the simulation step bound for the model (this keeps the state space small enough for model checking) */
#define MAX_STEPS 50

/* Define the minimum green time for the traffic light at each intersection (because the higher the min green time, the exponentially more states need to be explored) */
#define MIN_GREEN_TIME 3

#define isUturn(a, b) ( (a == LEFT  && b == RIGHT) || (a == RIGHT && b == LEFT) || (a == UP    && b == DOWN) || (a == DOWN  && b == UP) )

typedef IntersectionState {
    bool valid_light[5]; /* True if direction exists at intersection i */
    byte light_state[5]; /* light_state[i][d] is the current state of the light at intersection i in direction d */
    bool waiting[5]; /* waiting[i][d] is true if there is a vehicle waiting at intersection i in direction d */
    byte green_count[5]; /* green_count[i][d] counts how many times direction d has been granted green at intersection i */
}

/* shared state variables */
IntersectionState intersection_state[NUM_INTERSECTIONS]; /* per-intersection state stored as an array of structs */
byte active_green[NUM_INTERSECTIONS]; /* active_green[i] is the direction that currently has the green light at intersection i */
byte green_duration[NUM_INTERSECTIONS]; /* green_duration[i] is the number of steps the current green light has been active at intersection i */
byte last_green_set[NUM_INTERSECTIONS]; /* last_green_set[i] is the direction that was last set to green at intersection i */
bool served[NUM_VEHICLES]; /* true when vehicle has completed its route */
bool double_green_violation = false; /* flag to indicate if there is a double green violation */
bool min_green_violated = false; /* flag to indicate if there is a minimum green time violation */


/* Python Intersection Coordinates to Intersection IDs mapping
INTERSECTIONS = {
    "I1": (0, 0),
    "I2": (29, 0),
    "I3": (58, 0),
    "I4": (0, 29),
    "I5": (29, 29),
    "I6": (58, 29),
    "I7": (0, 58),
    "I8": (29, 58),
    "I9": (58, 58),
}
*/


/* Property 1: At every intersection, every vehicle eventually gets its turn of green signal. */
/* For each valid intersection direction pair, we check if a vehicle is waiting */
/* If there is a vehicle waiting, we check if it eventually gets a green light */

/* Pattern eventually = <> */
/* Pattern At every intersection = car at intersection and [] */
/* Pattern: [] (waiting[i][d] -> <> (light_state[i][d] == GREEN)) */

/* I1: UP, RIGHT are valid directions to come from */
ltl property1_I1_UP { [] (intersection_state[I1].waiting[UP] -> <> (intersection_state[I1].light_state[UP] == GREEN)) }
ltl property1_I1_RIGHT { [] (intersection_state[I1].waiting[RIGHT] -> <> (intersection_state[I1].light_state[RIGHT] == GREEN)) }

/* I2: UP, LEFT, RIGHT are valid directions to come from */
ltl property1_I2_UP { [] (intersection_state[I2].waiting[UP] -> <> (intersection_state[I2].light_state[UP] == GREEN)) }
ltl property1_I2_LEFT { [] (intersection_state[I2].waiting[LEFT] -> <> (intersection_state[I2].light_state[LEFT] == GREEN)) }
ltl property1_I2_RIGHT { [] (intersection_state[I2].waiting[RIGHT] -> <> (intersection_state[I2].light_state[RIGHT] == GREEN)) }

/* I3: UP, LEFT are valid directions to come from */
ltl property1_I3_UP { [] (intersection_state[I3].waiting[UP] -> <> (intersection_state[I3].light_state[UP] == GREEN)) }
ltl property1_I3_LEFT { [] (intersection_state[I3].waiting[LEFT] -> <> (intersection_state[I3].light_state[LEFT] == GREEN)) }

/* I4: UP, RIGHT, DOWN are valid directions to come from */
ltl property1_I4_UP { [] (intersection_state[I4].waiting[UP] -> <> (intersection_state[I4].light_state[UP] == GREEN)) }
ltl property1_I4_RIGHT { [] (intersection_state[I4].waiting[RIGHT] -> <> (intersection_state[I4].light_state[RIGHT] == GREEN)) }
ltl property1_I4_DOWN { [] (intersection_state[I4].waiting[DOWN] -> <> (intersection_state[I4].light_state[DOWN] == GREEN)) }

/* I5: UP, RIGHT, DOWN, LEFT are valid directions to come from */
ltl property1_I5_UP { [] (intersection_state[I5].waiting[UP] -> <> (intersection_state[I5].light_state[UP] == GREEN)) }
ltl property1_I5_RIGHT { [] (intersection_state[I5].waiting[RIGHT] -> <> (intersection_state[I5].light_state[RIGHT] == GREEN)) }
ltl property1_I5_DOWN { [] (intersection_state[I5].waiting[DOWN] -> <> (intersection_state[I5].light_state[DOWN] == GREEN)) }
ltl property1_I5_LEFT { [] (intersection_state[I5].waiting[LEFT] -> <> (intersection_state[I5].light_state[LEFT] == GREEN)) }

/* I6: UP, DOWN, LEFT are valid directions to come from */
ltl property1_I6_UP { [] (intersection_state[I6].waiting[UP] -> <> (intersection_state[I6].light_state[UP] == GREEN)) }
ltl property1_I6_DOWN { [] (intersection_state[I6].waiting[DOWN] -> <> (intersection_state[I6].light_state[DOWN] == GREEN)) }
ltl property1_I6_LEFT { [] (intersection_state[I6].waiting[LEFT] -> <> (intersection_state[I6].light_state[LEFT] == GREEN)) }

/* I7: RIGHT, DOWN are valid directions to come from */
ltl property1_I7_RIGHT { [] (intersection_state[I7].waiting[RIGHT] -> <> (intersection_state[I7].light_state[RIGHT] == GREEN)) }
ltl property1_I7_DOWN { [] (intersection_state[I7].waiting[DOWN] -> <> (intersection_state[I7].light_state[DOWN] == GREEN)) }

/* I8: DOWN, RIGHT, LEFT are valid directions to come from */
ltl property1_I8_UP { [] (intersection_state[I8].waiting[UP] -> <> (intersection_state[I8].light_state[UP] == GREEN)) }
ltl property1_I8_RIGHT { [] (intersection_state[I8].waiting[RIGHT] -> <> (intersection_state[I8].light_state[RIGHT] == GREEN)) }
ltl property1_I8_LEFT { [] (intersection_state[I8].waiting[LEFT] -> <> (intersection_state[I8].light_state[LEFT] == GREEN)) }

/* I9: DOWN, LEFT are valid directions to come from */
ltl property1_I9_DOWN { [] (intersection_state[I9].waiting[DOWN] -> <> (intersection_state[I9].light_state[DOWN] == GREEN)) }
ltl property1_I9_LEFT { [] (intersection_state[I9].waiting[LEFT] -> <> (intersection_state[I9].light_state[LEFT] == GREEN)) }


/* Property 2: At every intersection, the green signal is granted unconditionally fairly among all directions. */
/* every valid direction must receive green infinitely often even if other vehicles are waiting. */
/* Pattern infinitely often = [] <> */
/* Pattern: [] (waiting[i][d] -> <> (light_state[i][d] == GREEN))  */

/* I1: UP, RIGHT are valid directions to come from */
ltl property2_I1_UP { [] <> (intersection_state[I1].light_state[UP] == GREEN) }
ltl property2_I1_RIGHT { [] <> (intersection_state[I1].light_state[RIGHT] == GREEN) }

/* I2: UP, LEFT, RIGHT are valid directions to come from */
ltl property2_I2_UP { [] <> (intersection_state[I2].light_state[UP] == GREEN) }
ltl property2_I2_LEFT { [] <> (intersection_state[I2].light_state[LEFT] == GREEN) }
ltl property2_I2_RIGHT { [] <> (intersection_state[I2].light_state[RIGHT] == GREEN) }

/* I3: UP, LEFT are valid directions to come from */
ltl property2_I3_UP { [] <> (intersection_state[I3].light_state[UP] == GREEN) }
ltl property2_I3_LEFT { [] <> (intersection_state[I3].light_state[LEFT] == GREEN) }

/* I4: UP, RIGHT, DOWN are valid directions to come from */
ltl property2_I4_UP { [] <> (intersection_state[I4].light_state[UP] == GREEN) }
ltl property2_I4_RIGHT { [] <> (intersection_state[I4].light_state[RIGHT] == GREEN) }
ltl property2_I4_DOWN { [] <> (intersection_state[I4].light_state[DOWN] == GREEN) }

/* I5: UP, RIGHT, DOWN, LEFT are valid directions to come from */
ltl property2_I5_UP { [] <> (intersection_state[I5].light_state[UP] == GREEN) }
ltl property2_I5_RIGHT { [] <> (intersection_state[I5].light_state[RIGHT] == GREEN) }
ltl property2_I5_DOWN { [] <> (intersection_state[I5].light_state[DOWN] == GREEN) }
ltl property2_I5_LEFT { [] <> (intersection_state[I5].light_state[LEFT] == GREEN) }

/* I6: UP, DOWN, LEFT are valid directions to come from */
ltl property2_I6_UP { [] <> (intersection_state[I6].light_state[UP] == GREEN) }
ltl property2_I6_DOWN { [] <> (intersection_state[I6].light_state[DOWN] == GREEN) }
ltl property2_I6_LEFT { [] <> (intersection_state[I6].light_state[LEFT] == GREEN) }

/* I7: RIGHT, DOWN are valid directions to come from */
ltl property2_I7_RIGHT { [] <> (intersection_state[I7].light_state[RIGHT] == GREEN) }
ltl property2_I7_DOWN { [] <> (intersection_state[I7].light_state[DOWN] == GREEN) }

/* I8: DOWN, RIGHT, LEFT are valid directions to come from */
ltl property2_I8_UP { [] <> (intersection_state[I8].light_state[UP] == GREEN) }
ltl property2_I8_RIGHT { [] <> (intersection_state[I8].light_state[RIGHT] == GREEN) }
ltl property2_I8_LEFT { [] <> (intersection_state[I8].light_state[LEFT] == GREEN) }

/* I9: DOWN, LEFT are valid directions to come from */
ltl property2_I9_DOWN { [] <> (intersection_state[I9].light_state[DOWN] == GREEN) }
ltl property2_I9_LEFT { [] <> (intersection_state[I9].light_state[LEFT] == GREEN) }


/* Property 3: At any moment at any intersection, there is only one light is green. */
/* Use the double_green_violation flag to check if there is a state where more than one light is green at the same time */
/* Assert !double_green_violation to check that this never happens */
/* Pattern never = always not true = [] !flag */

ltl property3 { [] !double_green_violation }

/* Property 4: At every intersection, once the green is set, it stays green for at minimum green time units (10). */
/* Use the min_green_violated flag to check if there is a state where the green light changes before the minimum green time has elapsed */
/* Checked using two methods: */
/* Method 1: Check that min_green_violated is never violated */
/* Pattern never = always not true = [] !flag */
ltl property4_method1 { [] !min_green_violated }

/* Method 2: Check that if the green light active, and green duration is less than MIN_GREEN_TIME, then the next step must have the same active green light */
/* pattern always  (green duration < min green steps and active green[i] isn;t none -> next active green[i] is the same as last green set[i]) */
/* pattern : ltl property4_method2 { [] ( (green_duration[i] < MIN_GREEN_TIME && active_green[i] != NONE) -> X (active_green[i] == last_green_set[i]) ) } */
/* Check for each intersection */
/* ltl property4_method2_I1 { [] ( (green_duration[I1] < MIN_GREEN_TIME && active_green[I1] != NONE) -> X (active_green[I1] == last_green_set[I1]) ) } */
/* ltl property4_method2_I2 { [] ( (green_duration[I2] < MIN_GREEN_TIME && active_green[I2] != NONE) -> X (active_green[I2] == last_green_set[I2]) ) } */
/* ltl property4_method2_I3 { [] ( (green_duration[I3] < MIN_GREEN_TIME && active_green[I3] != NONE) -> X (active_green[I3] == last_green_set[I3]) ) } */
/* ltl property4_method2_I4 { [] ( (green_duration[I4] < MIN_GREEN_TIME && active_green[I4] != NONE) -> X (active_green[I4] == last_green_set[I4]) ) } */
/* ltl property4_method2_I5 { [] ( (green_duration[I5] < MIN_GREEN_TIME && active_green[I5] != NONE) -> X (active_green[I5] == last_green_set[I5]) ) } */
/* ltl property4_method2_I6 { [] ( (green_duration[I6] < MIN_GREEN_TIME && active_green[I6] != NONE) -> X (active_green[I6] == last_green_set[I6]) ) } */
/* ltl property4_method2_I7 { [] ( (green_duration[I7] < MIN_GREEN_TIME && active_green[I7] != NONE) -> X (active_green[I7] == last_green_set[I7]) ) } */
/* ltl property4_method2_I8 { [] ( (green_duration[I8] < MIN_GREEN_TIME && active_green[I8] != NONE) -> X (active_green[I8] == last_green_set[I8]) ) } */
/* ltl property4_method2_I9 { [] ( (green_duration[I9] < MIN_GREEN_TIME && active_green[I9] != NONE) -> X (active_green[I9] == last_green_set[I9]) ) } */

/* Function get next intersection: replaces add_step() and is_drivable() from python code */
inline getNextIntersection(cur, dir, nxt) {
    if
    :: cur == I1 && dir == UP    -> nxt = I4
    :: cur == I1 && dir == RIGHT -> nxt = I2
    :: cur == I2 && dir == UP    -> nxt = I5
    :: cur == I2 && dir == RIGHT -> nxt = I3
    :: cur == I2 && dir == LEFT  -> nxt = I1
    :: cur == I3 && dir == UP    -> nxt = I6
    :: cur == I3 && dir == LEFT  -> nxt = I2
    :: cur == I4 && dir == UP    -> nxt = I7
    :: cur == I4 && dir == RIGHT -> nxt = I5
    :: cur == I4 && dir == DOWN  -> nxt = I1
    :: cur == I5 && dir == UP    -> nxt = I8
    :: cur == I5 && dir == RIGHT -> nxt = I6
    :: cur == I5 && dir == DOWN  -> nxt = I2
    :: cur == I5 && dir == LEFT  -> nxt = I4
    :: cur == I6 && dir == UP    -> nxt = I9
    :: cur == I6 && dir == DOWN  -> nxt = I3
    :: cur == I6 && dir == LEFT  -> nxt = I5
    :: cur == I7 && dir == RIGHT -> nxt = I8
    :: cur == I7 && dir == DOWN  -> nxt = I4
    :: cur == I8 && dir == RIGHT -> nxt = I9
    :: cur == I8 && dir == DOWN  -> nxt = I5
    :: cur == I8 && dir == LEFT  -> nxt = I7
    :: cur == I9 && dir == DOWN  -> nxt = I6
    :: cur == I9 && dir == LEFT  -> nxt = I8
    :: else -> nxt = NONE
    fi
}

/* Initialization Process: initializes the state variables based on the infrastructure defined in the python code */
/* launches all concurrent processes for the traffic light controller and vehicles */
init {
    byte i;
    byte d;

    /* Initialize valid lights based on the infrastructure defined in the python code */
    /* I1: UP and RIGHT are valid directions to come from */
    intersection_state[I1].valid_light[UP] = true;
    intersection_state[I1].valid_light[RIGHT] = true;

    /* I2: UP, LEFT, RIGHT are valid directions to come from */
    intersection_state[I2].valid_light[UP] = true;
    intersection_state[I2].valid_light[LEFT] = true;
    intersection_state[I2].valid_light[RIGHT] = true;

    /* I3: UP, LEFT are valid directions to come from */
    intersection_state[I3].valid_light[UP] = true;
    intersection_state[I3].valid_light[LEFT] = true;
    /* I4: UP, RIGHT, DOWN are valid directions to come from */
    intersection_state[I4].valid_light[UP] = true;
    intersection_state[I4].valid_light[RIGHT] = true;
    intersection_state[I4].valid_light[DOWN] = true;

    /* I5: UP, RIGHT, DOWN, LEFT are valid directions to come from */
    intersection_state[I5].valid_light[UP] = true;
    intersection_state[I5].valid_light[RIGHT] = true;
    intersection_state[I5].valid_light[DOWN] = true;
    intersection_state[I5].valid_light[LEFT] = true;

    /* I6: UP, DOWN, LEFT are valid directions to come from */
    intersection_state[I6].valid_light[UP] = true;
    intersection_state[I6].valid_light[DOWN] = true;
    intersection_state[I6].valid_light[LEFT] = true;

    /* I7: RIGHT, DOWN are valid directions to come from */
    intersection_state[I7].valid_light[RIGHT] = true;
    intersection_state[I7].valid_light[DOWN] = true;

    /* I8: DOWN, RIGHT, LEFT are valid directions to come from */
    intersection_state[I8].valid_light[DOWN] = true;
    intersection_state[I8].valid_light[RIGHT] = true;
    intersection_state[I8].valid_light[LEFT] = true;

    /* I9: DOWN, LEFT are valid directions to come from */
    intersection_state[I9].valid_light[DOWN] = true;
    intersection_state[I9].valid_light[LEFT] = true;

    /* Initialize light_states, waiting, green_count, served arrays to default values */
    i = 0;
    do
    :: i < NUM_INTERSECTIONS ->
        d = 1;
        do
        :: d <= 4 ->
            intersection_state[i].light_state[d] = RED;
            intersection_state[i].waiting[d] = false;
            intersection_state[i].green_count[d] = 0;
            d++;
        :: d > 4 -> break
        od;
        active_green[i] = NONE;
        green_duration[i] = 0;
        last_green_set[i] = NONE;
        i++;
    :: i >= NUM_INTERSECTIONS -> break;
    od;

    i = 0;
    do
    :: i < NUM_VEHICLES ->
        served[i] = false;
        i++;
    :: i >= NUM_VEHICLES -> break;
    od;

    /* initialize green light flags */
    double_green_violation = false;
    min_green_violated = false;

    /* Launch all processes for vehicles and traffic light controllers */
    /* Launch 3 vehicles and 9 traffic light controllers */
    run VehicleProcess(0, I7, RIGHT, I9); /* Vehicle 0 starts at I7, wants to go RIGHT to I8, then RIGHT to I9 */
    run VehicleProcess(1, I1, UP, I7); /* Vehicle 1 starts at I1, wants to go UP to I4, then UP to I7 */
    run VehicleProcess(2, I3, LEFT, I1); /* Vehicle 2 starts at I3, wants to go LEFT to I2, then LEFT to I1 */
    
    run TrafficLightController(I1);
    run TrafficLightController(I2);
    run TrafficLightController(I3);
    run TrafficLightController(I4);
    run TrafficLightController(I5);
    run TrafficLightController(I6);
    run TrafficLightController(I7);
    run TrafficLightController(I8);
    run TrafficLightController(I9);

    /* Launch monitor process to check for double green violation and minimum green time violation */
    run MonitorProcess();
}


/* Light Controller Process: controls the traffic light at each intersection */
/* Mirrors update_lights() logic from the python code, but simplified for the model */
/* 1. No active green -> non-deterministically choose a valid direction to set green */
/* Min time not elapsed -> keep current green */
/* Min time elapsed -> non-deterministically choose to keep current green or switch to a different valid direction */

/* Non-determinism lets SPIN explore all possible scheduling decisions which covers demand based scheduler from python code */
proctype TrafficLightController(byte node) {
    byte d;
    byte step = 0; /* How long green has been active */

    do
    :: step >= MAX_STEPS -> break

    :: step < MAX_STEPS ->
        /* choose next green direction */
        if
        
        /* No active green, choose a valid direction to set green */
        :: active_green[node] == NONE ->
            if
            /* Check for valid directions */
            :: intersection_state[node].valid_light[UP] -> d = UP
            :: intersection_state[node].valid_light[RIGHT] -> d = RIGHT
            :: intersection_state[node].valid_light[DOWN] -> d = DOWN
            :: intersection_state[node].valid_light[LEFT] -> d = LEFT
            fi;

        /* Min green time not elapsed, keep current green */
        :: (active_green[node] != NONE && green_duration[node] < MIN_GREEN_TIME) ->
            d = active_green[node];

        /* Min green time elapsed, can choose to keep current green or switch */
        :: (active_green[node] != NONE && green_duration[node] >= MIN_GREEN_TIME) ->
            if
            /* stay on current green */
            :: d = active_green[node] /* keep current green */
            /* switch to a different valid direction */
            :: intersection_state[node].valid_light[UP] && active_green[node] != UP -> d = UP
            :: intersection_state[node].valid_light[RIGHT] && active_green[node] != RIGHT -> d = RIGHT
            :: intersection_state[node].valid_light[DOWN] && active_green[node] != DOWN -> d = DOWN
            :: intersection_state[node].valid_light[LEFT] && active_green[node] != LEFT -> d = LEFT
            fi;
        fi;

        atomic {
            /* Property 4 violation check: if green light changes before minimum green time, set min_green_violated to true */
            if
            :: active_green[node] != NONE && d != active_green[node] && green_duration[node] < MIN_GREEN_TIME ->
                min_green_violated = true;
                assert(false) /* fail immediately if min green time violation is detected */
            :: else -> skip
            fi;

            /* Update duration counters */
            if 
            /* If green is staying the same, increment duration */
            :: active_green[node] == d -> green_duration[node]++
            /* If green is changing, reset duration and update last green set */
            :: active_green[node] != d ->
                green_duration[node] = 1;
                active_green[node] = d;
            fi;

            /* Update light states */
            byte dd;
            dd = 1;
            do
            :: dd <= 4 ->
                if
                :: intersection_state[node].valid_light[dd] && dd == d -> intersection_state[node].light_state[dd] = GREEN
                :: intersection_state[node].valid_light[dd] && dd != d -> intersection_state[node].light_state[dd] = RED
                :: !intersection_state[node].valid_light[dd] -> skip
                fi;
                dd++
            :: dd > 4 -> break
            od;

            last_green_set[node] = d;

            /* add to green count if it isn't too high */
            if
            :: intersection_state[node].green_count[d] < 255 -> intersection_state[node].green_count[d]++
            :: else -> skip
            fi;
        };
        step++;
    od;
}


/* Vehicle Process: models the behavior of each vehicle in the system */
/* Each vehicle has a predefined route (for simplicity, we hardcode the routes for 3 vehicles based on the python code) */
/* Each vehicle process checks if it can move at each step based on the traffic light state and updates the waiting status accordingly */
proctype VehicleProcess(byte vid; byte start_int; byte start_dir; byte dest_int) {
    byte pos = start_int;
    byte dir = start_dir;
    byte next = NONE;
    byte step = 0;

    /* step limit reached, stop the process */
    do
    :: step >= MAX_STEPS -> break

    /* termination: vehicle has reached destination */
    :: pos == dest_int ->
        served[vid] = true;
        break;

    /* Normal movement step */
    :: step < MAX_STEPS && pos != dest_int ->
        /* Set waiting so property 1 can check if vehicle is waiting at an intersection */
        atomic {
            if
            :: intersection_state[pos].light_state[dir] == RED ->
                intersection_state[pos].waiting[dir] = true;
            :: intersection_state[pos].light_state[dir] == GREEN -> skip
            fi;
            
            intersection_state[pos].waiting[dir] = false;
            getNextIntersection(pos, dir, next);
            
            /* Move to next if it exists, otherwise stay put */
            if
            :: next != NONE -> pos = next
            :: next == NONE -> skip    /* stay at current position */
            fi
        };

        /* Check if we should stop AFTER atomic block */
        if
        :: next == NONE -> break    /* now properly exits with served[] set */
        :: next != NONE -> skip
        fi;

        /* Choose direction at new intersection */
        if
        :: intersection_state[pos].valid_light[UP] && !isUturn(dir, UP) -> dir = UP
        :: intersection_state[pos].valid_light[RIGHT] && !isUturn(dir, RIGHT) -> dir = RIGHT
        :: intersection_state[pos].valid_light[DOWN] && !isUturn(dir, DOWN) -> dir = DOWN
        :: intersection_state[pos].valid_light[LEFT] && !isUturn(dir, LEFT) -> dir = LEFT
        fi;

        step++;
    od;
    intersection_state[pos].waiting[dir] = false; /* clear waiting status when vehicle process ends */
    served[vid] = true; /* mark vehicle as served when it finishes its route or reaches step limit */
}

/* Monitor Process: checks for double green violation and minimum green time violation */
/* This process runs concurrently and continuously checks the state of the traffic lights to set the violation flags if any violation is detected */
proctype MonitorProcess() {
    byte i;
    byte d;
    byte count;

    do
    :: true ->
        /* check for double green violation: if more than one light is green at the same time at any intersection, set double_green_violation to true */
        i = 0;
        do
        /* go to each intersection */
        :: i < NUM_INTERSECTIONS ->
            count = 0;
            d = 1;
            do
            /* check each direction for a green light and update count */
            :: d <= 4 ->
                if
                :: intersection_state[i].valid_light[d] && intersection_state[i].light_state[d] == GREEN -> count++
                :: else -> skip
                fi;
                d++
            :: d > 4 -> break
            od;
            /* counts more than 1 green light, set violation flag */
            if
            :: count > 1 -> 
                double_green_violation = true;
                assert(false) /* fail immediately if double green violation is detected */
            :: else -> skip
            fi;
            i++;
        :: i >= NUM_INTERSECTIONS -> break
        od
    od;
}