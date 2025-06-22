#!/usr/bin/env python3
from cmath import pi
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
import termios
import sys
import tty
import select

class TrackController(Node):
    def __init__(self):
        super().__init__('track_controller')
        
        # Публикаторы для управления треками
        self.forward_pub = self.create_publisher(Float64MultiArray, '/forward_track_controller/commands', 10)
        self.backward_pub = self.create_publisher(Float64MultiArray, '/backward_track_controller/commands', 10)
        
        # Текущие позиции
        self.forward_pos = 0.0
        self.backward_pos = 0.0
        
        # Шаг изменения позиции
        self.step = 0.05
        
        print("Управление треками:")
        print("  W/S - передний трек")
        print("  A/D - задний трек")
        print("  Q - выход")
        
        # Сохраняем оригинальные настройки терминала
        self.old_attr = termios.tcgetattr(sys.stdin)
        tty.setcbreak(sys.stdin.fileno())
        
        # Таймер для проверки нажатий
        self.timer = self.create_timer(0.1, self.check_key)
    
    def check_key(self):
        try:
            # Проверяем, есть ли ввод
            if select.select([sys.stdin], [], [], 0)[0]:
                key = sys.stdin.read(1)
                if key == 'q':
                    self.cleanup()
                    rclpy.shutdown()
                    return
                elif key == 'w':
                    self.forward_pos = min(self.forward_pos + self.step, pi/2)
                elif key == 's':
                    self.forward_pos = max(self.forward_pos - self.step, -pi/2)
                elif key == 'd':
                    self.backward_pos = min(self.backward_pos + self.step, pi/2)
                elif key == 'a':
                    self.backward_pos = max(self.backward_pos - self.step, -pi/2)
                
                # Отправка команд
                self.publish_command(self.forward_pub, self.forward_pos)
                self.publish_command(self.backward_pub, self.backward_pos)
                
                print(f"Передний: {self.forward_pos:.2f} | Задний: {self.backward_pos:.2f}")
                
        except Exception as e:
            print(f"Ошибка: {e}")
    
    def publish_command(self, publisher, position):
        msg = Float64MultiArray()
        msg.data = [position]
        publisher.publish(msg)
        self.get_logger().info(f"Отправлено: {position}")
    
    def cleanup(self):
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_attr)
        self.timer.cancel()

def main(args=None):
    rclpy.init(args=args)
    node = TrackController()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.cleanup()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()