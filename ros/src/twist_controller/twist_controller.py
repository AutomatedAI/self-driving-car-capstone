import rospy
from   yaw_controller import YawController
from   pid            import PID


class Controller(object):

    def __init__(self):
        max_lat_accel       = rospy.get_param('~max_lat_accel',   3.0)
        max_steer_angle     = rospy.get_param('~max_steer_angle', 8.0)        
        steer_ratio         = rospy.get_param('~steer_ratio',     2.67)
        wheel_base          = rospy.get_param('~wheel_base',      3.0)
        self.brake_deadband = rospy.get_param('~brake_deadband',  0.2)

        self.last_time   = None
        self.pid_control = PID(5.0, 0.1, 0.02)
        self.yaw_control = YawController(wheel_base=3.0, 
                                         steer_ratio=2.67,
                                         min_speed=0.0, 
                                         max_lat_accel=3.0,
                                         max_steer_angle=8.0)    

        self.yaw_pid_control = PID(5.0, 1.5, 0.15)
        # self.yaw_pid_control = PID(5.0, 2.5, 0.10)


    def control(self, **kwargs):
        dbw_enabled = kwargs['dbw_enabled']

        tc_l = kwargs['twist_cmd'].twist.linear
        tc_a = kwargs['twist_cmd'].twist.angular

        cv_l = kwargs['current_velocity'].twist.linear
        cv_a = kwargs['current_velocity'].twist.angular

        velocity_error           = tc_l.x - cv_l.x
        desired_linear_velocity  = tc_l.x
        desired_angular_velocity = tc_a.z
        current_linear_velocity  = cv_l.x
        current_angular_velocity = cv_a.z        
   
        
        if dbw_enabled is False:
            self.pid_control.reset()
            self.yaw_pid_control.reset()
           
        if self.last_time is not None:
            time           = rospy.get_time()
            delta_t        = time - self.last_time
            self.last_time = time

            control  = self.pid_control.update(velocity_error, delta_t)
            throttle = max(0.0, control)
            brake    = max(0.0, -control) + self.brake_deadband


            desired_steering = self.yaw_control.get_steering(desired_linear_velocity, 
                                                     desired_angular_velocity, 
                                                     current_linear_velocity)

            current_steering = self.yaw_control.get_steering(desired_linear_velocity, 
                                                     current_angular_velocity, 
                                                     current_linear_velocity)
            
            #TODO add low pass filter to desired_trajectory
            
            steering_error = desired_steering - current_steering

            steering  = self.yaw_pid_control.update(steering_error, delta_t)
            rospy.logwarn('steering: ' + str(steering))

            return throttle, brake, steering

        else:
            self.last_time = rospy.get_time()
            return 0.0, 0.0, 0.0

