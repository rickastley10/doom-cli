import math
import time

class CLIDoom:
    def __init__(self):
        self.width = 60
        self.height = 20
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
            [3.5, 3.5, True],
            [8.5, 3.5, True], 
        ]
        
        self.health = 100
        self.ammo = 20
        self.score = 0

    def cast_ray(self, angle):
        ray_x = self.player_x
        ray_y = self.player_y
        ray_dir_x = math.cos(angle)
        ray_dir_y = math.sin(angle)
        map_x, map_y = int(ray_x), int(ray_y)
        
        delta_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
        
        if ray_dir_x < 0:
            step_x = -1
            dist_x = (ray_x - map_x) * delta_x
        else:
            step_x = 1
            dist_x = (map_x + 1.0 - ray_x) * delta_x
            
        if ray_dir_y < 0:
            step_y = -1
            dist_y = (ray_y - map_y) * delta_y
        else:
            step_y = 1
            dist_y = (map_y + 1.0 - ray_y) * delta_y
        
        for _ in range(20):
            if dist_x < dist_y:
                dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                dist_y += delta_y
                map_y += step_y
                side = 1
            
            if self.map[map_y][map_x] == '#':
                if side == 0:
                    return (map_x - ray_x + (1 - step_x) / 2) / ray_dir_x
                else:
                    return (map_y - ray_y + (1 - step_y) / 2) / ray_dir_y
        return None

    def render(self):
        screen = []
        for x in range(self.width):
            ray_angle = self.player_angle + (2 * x / self.width - 1) * self.fov
            dist = self.cast_ray(ray_angle)
            
            if dist:
                height = min(self.height, int(self.height / (dist + 0.001)))
                ceiling = (self.height - height) // 2
                wall_char = '█' if dist < 3 else '▓' if dist < 6 else '▒'
                
                column = [' '] * ceiling + [wall_char] * height + ['.'] * (self.height - ceiling - height)
                screen.append(column)
            else:
                screen.append([' '] * (self.height//2) + ['.'] * (self.height//2))
        
        # Build display
        display = []
        for y in range(self.height):
            line = ''.join(screen[x][y] for x in range(self.width))
            display.append(line)
        
        # HUD
        display.append('=' * self.width)
        display.append(f"Health: {self.health} Ammo: {self.ammo} Score: {self.score}")
        display.append("WASD=Move JL=Turn SPACE=Shoot Q=Quit")
        return '\n'.join(display)

    def move(self, dx, dy):
        new_x = self.player_x + dx
        new_y = self.player_y + dy
        if self.map[int(new_y)][int(new_x)] != '#':
            self.player_x = new_x
            self.player_y = new_y

    def shoot(self):
        if self.ammo > 0:
            self.ammo -= 1
            for enemy in self.enemies:
                if enemy[2]:
                    dx = enemy[0] - self.player_x
                    dy = enemy[1] - self.player_y
                    dist = math.sqrt(dx*dx + dy*dy)
                    angle = math.atan2(dy, dx)
                    if abs(angle - self.player_angle) < 0.3 and dist < 5:
                        enemy[2] = False
                        self.score += 100
                        self.ammo += 10
                        break

    def update_enemies(self):
        for enemy in self.enemies:
            if enemy[2]:
                dx = self.player_x - enemy[0]
                dy = self.player_y - enemy[1]
                dist = math.sqrt(dx*dx + dy*dy)
                if dist > 0.5:
                    enemy[0] += dx / dist * 0.05
                    enemy[1] += dy / dist * 0.05
                if dist < 2 and int(time.time() * 10) % 20 == 0:
                    self.health -= 0

    def run(self):
        print("\n" * 50)
        print("CLI DOOM - Use WASD JL SPACE Q")
        
        while self.health > 0:
            # Show game immediately
            frame = self.render()
            print("\n" * 50)
            print(frame)
            
            # Get input
            try:
                key = input("> ").lower().strip()
            except:
                break
            
            # Handle input
            if key == 'q': break
            elif key == 'w': self.move(math.cos(self.player_angle)*0.3, math.sin(self.player_angle)*0.3)
            elif key == 's': self.move(-math.cos(self.player_angle)*0.3, -math.sin(self.player_angle)*0.3)
            elif key == 'a': self.move(math.cos(self.player_angle-math.pi/2)*0.2, math.sin(self.player_angle-math.pi/2)*0.2)
            elif key == 'd': self.move(math.cos(self.player_angle+math.pi/2)*0.2, math.sin(self.player_angle+math.pi/2)*0.2)
            elif key == 'j': self.player_angle -= 0.5
            elif key == 'l': self.player_angle += 0.5
            elif key == ' ': self.shoot()
            
            self.player_angle %= 2 * math.pi
            self.update_enemies()
            
            # Win condition
            if all(not e[2] for e in self.enemies):
                print("\nYOU WIN! Score:", self.score)
                break
        
        if self.health <= 0:
            print("\nGAME OVER! Score:", self.score)

if __name__ == "__main__":
    game = CLIDoom()
    game.run()
