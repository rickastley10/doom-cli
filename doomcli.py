import math
import os
import sys
import time
from collections import deque
import random

try:
    import msvcrt
except ImportError:
    import select
    import termios

class CLIDoom:
    def __init__(self, width=80, height=24):
        self.width = width
        self.height = height
        self.player_x = 1.5
        self.player_y = 1.5
        self.player_angle = 0
        self.fov = math.pi / 3
        self.map = [
            "############",
            "#..........#",
            "#..........#",
            "#....##....#",
            "#....##....#",
            "#..........#",
            "#..........#",
            "#..........#",
            "#..........#",
            "############"
        ]
        self.enemies = [
            {'x': 3.5, 'y': 3.5, 'alive': True, 'type': 'Z'},
            {'x': 8.5, 'y': 3.5, 'alive': True, 'type': 'D'},
            {'x': 5.5, 'y': 7.5, 'alive': True, 'type': 'M'}
        ]
        self.health = 100
        self.ammo = 30
        self.score = 0
        self.game_over = False
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_char(self):
        """Get a single character from input without requiring Enter"""
        try:
            if os.name == 'nt':
                if msvcrt.kbhit():
                    return msvcrt.getch().decode()
            else:
                if select.select([sys.stdin], [], [], 0) == ([sys.stdin], [], []):
                    return sys.stdin.read(1)
        except:
            pass
        return ''
    
    def cast_ray(self, angle):
        """Cast a ray and return distance to wall and wall type"""
        ray_x = self.player_x
        ray_y = self.player_y
        
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)
        
        map_x, map_y = int(ray_x), int(ray_y)
        
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
        
        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (ray_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - ray_x) * delta_dist_x
            
        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (ray_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - ray_y) * delta_dist_y
        
        hit = False
        side = 0
        
        while not hit:
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            if (map_x < 0 or map_x >= len(self.map[0]) or 
                map_y < 0 or map_y >= len(self.map)):
                break
                
            if self.map[map_y][map_x] == '#':
                hit = True
        
        if hit:
            if side == 0:
                perp_wall_dist = (map_x - ray_x + (1 - step_x) / 2) / ray_dir_x
            else:
                perp_wall_dist = (map_y - ray_y + (1 - step_y) / 2) / ray_dir_y
            
            return perp_wall_dist, side
        return None, None
    
    def render_frame(self):
        """Render one frame of the game"""
        output = []
        
        # Raycasting view
        for x in range(self.width):
            camera_x = 2 * x / self.width - 1
            ray_angle = self.player_angle + self.fov * camera_x
            
            dist, side = self.cast_ray(ray_angle)
            
            if dist is not None:
                # Calculate wall height
                line_height = int(self.height / (dist + 0.001))
                
                # Choose wall character based on distance and side
                if dist < 2:
                    wall_char = '█' if side == 0 else '▒'
                elif dist < 4:
                    wall_char = '▓' if side == 0 else '░'
                elif dist < 6:
                    wall_char = '▒'
                else:
                    wall_char = '░'
                
                # Draw the column
                column = []
                for y in range(self.height):
                    if y < (self.height - line_height) // 2:
                        # Sky
                        column.append(' ')
                    elif y < (self.height + line_height) // 2:
                        # Wall
                        column.append(wall_char)
                    else:
                        # Floor
                        floor_char = '.' if (x + y) % 4 == 0 else ' '
                        column.append(floor_char)
                output.append(column)
            else:
                # No wall hit, draw sky and floor
                column = []
                for y in range(self.height):
                    if y < self.height // 2:
                        column.append(' ')
                    else:
                        floor_char = '.' if (x + y) % 4 == 0 else ' '
                        column.append(floor_char)
                output.append(column)
        
        # Transpose for display
        display = []
        for y in range(self.height):
            row = []
            for x in range(self.width):
                row.append(output[x][y])
            display.append(''.join(row))
        
        # Add HUD
        hud_line = f"Health: {self.health} | Ammo: {self.ammo} | Score: {self.score}"
        hud_line = hud_line.ljust(self.width)[:self.width]
        display.append('=' * self.width)
        display.append(hud_line)
        display.append("WASD: Move | Mouse: Aim | SPACE: Shoot | Q: Quit")
        
        return '\n'.join(display)
    
    def move_player(self, dx, dy):
        """Move player with collision detection"""
        new_x = self.player_x + dx
        new_y = self.player_y + dy
        
        # Check collision with walls
        if (0 <= int(new_x) < len(self.map[0]) and 
            0 <= int(new_y) < len(self.map) and 
            self.map[int(new_y)][int(new_x)] != '#'):
            self.player_x = new_x
            self.player_y = new_y
    
    def shoot(self):
        """Handle shooting"""
        if self.ammo <= 0:
            return
            
        self.ammo -= 1
        
        # Check if we hit an enemy
        for enemy in self.enemies:
            if not enemy['alive']:
                continue
                
            # Simple distance check in view direction
            dx = enemy['x'] - self.player_x
            dy = enemy['y'] - self.player_y
            dist = math.sqrt(dx*dx + dy*dy)
            
            # Angle to enemy
            angle_to_enemy = math.atan2(dy, dx)
            angle_diff = abs(angle_to_enemy - self.player_angle)
            
            if angle_diff < 0.3 and dist < 5:  # In field of view and range
                enemy['alive'] = False
                self.score += 100
                break
    
    def update_enemies(self):
        """Update enemy positions and attacks"""
        for enemy in self.enemies:
            if not enemy['alive']:
                continue
                
            # Simple movement towards player
            dx = self.player_x - enemy['x']
            dy = self.player_y - enemy['y']
            dist = math.sqrt(dx*dx + dy*dy)
            
            if dist > 0.5:  # Don't get too close
                enemy['x'] += dx / dist * 0.05
                enemy['y'] += dy / dist * 0.05
            
            # Random chance to damage player
            if dist < 2 and random.random() < 0.01:
                self.health -= 5
                if self.health <= 0:
                    self.game_over = True
    
    def run(self):
        """Main game loop"""
        if os.name != 'nt':
            # Set up non-blocking input for Unix
            old_settings = termios.tcgetattr(sys.stdin)
            try:
                tty.setraw(sys.stdin.fileno())
            except:
                pass
        
        try:
            while not self.game_over:
                self.clear_screen()
                
                # Handle input
                key = self.get_char().lower()
                
                if key == 'q':
                    break
                elif key == 'w':
                    self.move_player(math.cos(self.player_angle) * 0.2, 
                                   math.sin(self.player_angle) * 0.2)
                elif key == 's':
                    self.move_player(-math.cos(self.player_angle) * 0.2, 
                                   -math.sin(self.player_angle) * 0.2)
                elif key == 'a':
                    self.move_player(math.cos(self.player_angle - math.pi/2) * 0.2,
                                   math.sin(self.player_angle - math.pi/2) * 0.2)
                elif key == 'd':
                    self.move_player(math.cos(self.player_angle + math.pi/2) * 0.2,
                                   math.sin(self.player_angle + math.pi/2) * 0.2)
                elif key == ' ':
                    self.shoot()
                elif key == 'j':  # Turn left
                    self.player_angle -= 0.2
                elif key == 'l':  # Turn right
                    self.player_angle += 0.2
                
                # Keep angle normalized
                self.player_angle %= 2 * math.pi
                
                # Update game state
                self.update_enemies()
                
                # Render and display
                frame = self.render_frame()
                print(frame)
                
                # Check win condition
                if all(not e['alive'] for e in self.enemies):
                    print("\n" + "="*self.width)
                    print("VICTORY! All enemies defeated!".center(self.width))
                    print("="*self.width)
                    break
                
                time.sleep(0.05)
                
        finally:
            if os.name != 'nt':
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
        
        if self.game_over:
            print("\n" + "="*self.width)
            print("GAME OVER".center(self.width))
            print("="*self.width)

def main():
    print("CLI DOOM - ASCII Edition")
    print("=" * 40)
    print("Controls:")
    print("WASD - Move")
    print("J/L  - Turn left/right") 
    print("SPACE- Shoot")
    print("Q    - Quit")
    print("\nPress any key to start...")
    
    input()
    
    game = CLIDoom()
    game.run()

if __name__ == "__main__":
    main()

