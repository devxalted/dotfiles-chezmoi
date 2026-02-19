#!/usr/bin/env python3
"""
Cloudflare Tunnel Manager CLI
Manage Cloudflare tunnels with background process support
"""

import os
import sys
import subprocess
import signal
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class TunnelManager:
    def __init__(self, cert_file: Optional[str] = None, auto_select_cert: bool = True):
        self.pid_dir = Path("/tmp")
        self.config_dir = Path.home() / ".cloudflared"
        self.cert_file = cert_file
        
        # If no cert specified, try to find one
        if not self.cert_file and auto_select_cert:
            # Check for default cert.pem first
            default_cert = self.config_dir / "cert.pem"
            if default_cert.exists():
                self.cert_file = str(default_cert)
            else:
                # Look for any .pem file
                cert_files = list(self.config_dir.glob("*-cert.pem"))
                if cert_files:
                    self.cert_file = str(cert_files[0])
                    if len(cert_files) > 1:
                        print(f"{Colors.YELLOW}Multiple cert files found. Using: {cert_files[0].name}{Colors.ENDC}")
                        print(f"Available certs: {', '.join(f.name for f in cert_files)}")
        
    def get_pid_file(self, tunnel_name: str) -> Path:
        """Get PID file path for a tunnel"""
        return self.pid_dir / f"cloudflared-{tunnel_name}.pid"
    
    def get_log_file(self, tunnel_name: str) -> Path:
        """Get log file path for a tunnel"""
        return self.pid_dir / f"cloudflared-{tunnel_name}.log"
    
    def list_tunnels(self) -> List[Dict]:
        """List all Cloudflare tunnels"""
        try:
            cmd = ["cloudflared", "tunnel"]
            
            # Add cert file if specified
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            
            cmd.extend(["list", "--output", "json"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            tunnels = json.loads(result.stdout)
            return tunnels if tunnels else []
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error listing tunnels: {e}{Colors.ENDC}")
            if e.stderr:
                print(f"{Colors.RED}Error details: {e.stderr}{Colors.ENDC}")
            return []
        except json.JSONDecodeError:
            print(f"{Colors.RED}Error parsing tunnel list{Colors.ENDC}")
            return []
    
    def is_tunnel_running(self, tunnel_name: str) -> Tuple[bool, Optional[int]]:
        """Check if a tunnel is running and return its PID"""
        pid_file = self.get_pid_file(tunnel_name)
        
        if pid_file.exists():
            try:
                with open(pid_file, 'r') as f:
                    pid = int(f.read().strip())
                
                # Check if process is actually running using kill -0
                try:
                    os.kill(pid, 0)
                    # Verify it's actually a cloudflared process
                    try:
                        result = subprocess.run(
                            ["ps", "-p", str(pid), "-o", "comm="],
                            capture_output=True,
                            text=True
                        )
                        if 'cloudflared' in result.stdout:
                            return True, pid
                    except:
                        pass
                except (OSError, ProcessLookupError):
                    # Process doesn't exist
                    pass
                
                # PID file exists but process is not running
                pid_file.unlink()
            except (ValueError, IOError):
                if pid_file.exists():
                    pid_file.unlink()
        
        # Also check for any cloudflared processes running this tunnel
        try:
            result = subprocess.run(
                ["pgrep", "-f", f"cloudflared.*tunnel.*run.*{tunnel_name}"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0 and result.stdout.strip():
                pids = result.stdout.strip().split('\n')
                if pids and pids[0]:
                    return True, int(pids[0])
        except:
            pass
        
        return False, None
    
    def start_tunnel(self, tunnel_name: str, config_file: Optional[str] = None) -> bool:
        """Start a tunnel in the background"""
        running, pid = self.is_tunnel_running(tunnel_name)
        if running:
            print(f"{Colors.YELLOW}Tunnel '{tunnel_name}' is already running (PID: {pid}){Colors.ENDC}")
            return False
        
        pid_file = self.get_pid_file(tunnel_name)
        log_file = self.get_log_file(tunnel_name)
        
        # If no config file specified, look for tunnel-specific config
        if not config_file:
            default_config = self.config_dir / f"{tunnel_name}.yml"
            if default_config.exists():
                config_file = str(default_config)
            else:
                print(f"{Colors.YELLOW}Warning: No config file found for tunnel '{tunnel_name}'{Colors.ENDC}")
                print(f"Expected at: {default_config}")
        
        # Build command
        cmd = ["cloudflared", "tunnel"]
        if config_file and Path(config_file).exists():
            cmd.extend(["--config", config_file])
        cmd.extend(["run", tunnel_name])
        
        try:
            # Start process in background
            with open(log_file, 'w') as log:
                process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    start_new_session=True
                )
            
            # Save PID
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))
            
            # Wait a moment to check if it started successfully
            time.sleep(2)
            
            if process.poll() is None:
                print(f"{Colors.GREEN}✓ Started tunnel '{tunnel_name}' (PID: {process.pid}){Colors.ENDC}")
                print(f"  Log file: {log_file}")
                return True
            else:
                print(f"{Colors.RED}✗ Failed to start tunnel '{tunnel_name}'{Colors.ENDC}")
                print(f"  Check log file: {log_file}")
                if pid_file.exists():
                    pid_file.unlink()
                return False
                
        except Exception as e:
            print(f"{Colors.RED}Error starting tunnel: {e}{Colors.ENDC}")
            if pid_file.exists():
                pid_file.unlink()
            return False
    
    def stop_tunnel(self, tunnel_name: str) -> bool:
        """Stop a running tunnel"""
        running, pid = self.is_tunnel_running(tunnel_name)
        
        if not running:
            print(f"{Colors.YELLOW}Tunnel '{tunnel_name}' is not running{Colors.ENDC}")
            return False
        
        try:
            # Send SIGTERM for graceful shutdown
            os.kill(pid, signal.SIGTERM)
            
            # Wait for process to terminate (max 10 seconds)
            for _ in range(10):
                try:
                    os.kill(pid, 0)  # Check if process still exists
                    time.sleep(1)
                except (OSError, ProcessLookupError):
                    # Process no longer exists
                    break
            else:
                # Force kill if still running
                try:
                    os.kill(pid, signal.SIGKILL)
                    time.sleep(1)
                except:
                    pass
            
            # Clean up PID file
            pid_file = self.get_pid_file(tunnel_name)
            if pid_file.exists():
                pid_file.unlink()
            
            print(f"{Colors.GREEN}✓ Stopped tunnel '{tunnel_name}' (PID: {pid}){Colors.ENDC}")
            return True
            
        except ProcessLookupError:
            # Process already terminated
            pid_file = self.get_pid_file(tunnel_name)
            if pid_file.exists():
                pid_file.unlink()
            print(f"{Colors.GREEN}✓ Tunnel '{tunnel_name}' stopped{Colors.ENDC}")
            return True
        except Exception as e:
            print(f"{Colors.RED}Error stopping tunnel: {e}{Colors.ENDC}")
            return False
    
    def restart_tunnel(self, tunnel_name: str, config_file: Optional[str] = None) -> bool:
        """Restart a tunnel"""
        print(f"{Colors.CYAN}Restarting tunnel '{tunnel_name}'...{Colors.ENDC}")
        
        # Stop if running
        running, _ = self.is_tunnel_running(tunnel_name)
        if running:
            if not self.stop_tunnel(tunnel_name):
                return False
            time.sleep(2)  # Brief pause before restart
        
        # Start tunnel
        return self.start_tunnel(tunnel_name, config_file)
    
    def show_status(self):
        """Show status of all tunnels"""
        tunnels = self.list_tunnels()
        
        if not tunnels:
            print(f"{Colors.YELLOW}No tunnels found{Colors.ENDC}")
            return
        
        print(f"\n{Colors.BOLD}{Colors.HEADER}Cloudflare Tunnels Status{Colors.ENDC}")
        print("=" * 80)
        
        for tunnel in tunnels:
            name = tunnel.get('name', 'Unknown')
            tunnel_id = tunnel.get('id', 'Unknown')
            created = tunnel.get('created_at', 'Unknown')
            
            running, pid = self.is_tunnel_running(name)
            
            status_color = Colors.GREEN if running else Colors.RED
            status_text = f"Running (PID: {pid})" if running else "Stopped"
            
            print(f"\n{Colors.BOLD}Tunnel: {name}{Colors.ENDC}")
            print(f"  ID:      {tunnel_id}")
            print(f"  Created: {created}")
            print(f"  Status:  {status_color}{status_text}{Colors.ENDC}")
            
            if running:
                log_file = self.get_log_file(name)
                if log_file.exists():
                    print(f"  Log:     {log_file}")
        
        print("\n" + "=" * 80)
    
    def tail_logs(self, tunnel_name: str, lines: int = 50):
        """Tail the logs of a tunnel"""
        log_file = self.get_log_file(tunnel_name)
        
        if not log_file.exists():
            print(f"{Colors.YELLOW}No log file found for tunnel '{tunnel_name}'{Colors.ENDC}")
            return
        
        try:
            subprocess.run(["tail", "-n", str(lines), str(log_file)])
        except Exception as e:
            print(f"{Colors.RED}Error reading logs: {e}{Colors.ENDC}")
    
    def create_tunnel(self, tunnel_name: str, port: int, url: str, auto_start: bool = True, domain_selection: str = None) -> bool:
        """Create a new tunnel and configure it to route to a local port"""
        try:
            # First check if tunnel already exists
            tunnels = self.list_tunnels()
            if any(t.get('name') == tunnel_name for t in tunnels):
                print(f"{Colors.YELLOW}Tunnel '{tunnel_name}' already exists{Colors.ENDC}")
                return False
            
            # Extract domain from URL if not specified
            if not domain_selection:
                # Extract base domain from URL (e.g., "subdomain.example.com" -> "example.com")
                import re
                domain_match = re.search(r'([^.]+\.[^.]+)$', url)
                if domain_match:
                    domain_selection = domain_match.group(1)
            
            # Create the tunnel
            print(f"{Colors.CYAN}Creating tunnel '{tunnel_name}'...{Colors.ENDC}")
            cmd = ["cloudflared", "tunnel"]
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            cmd.extend(["create", tunnel_name])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"{Colors.GREEN}✓ Created tunnel '{tunnel_name}'{Colors.ENDC}")
            
            # Get the tunnel ID by querying the tunnel list
            tunnel_id = None
            cmd = ["cloudflared", "tunnel"]
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            cmd.extend(["list", "--output", "json"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            tunnels_data = json.loads(result.stdout)
            for tunnel in tunnels_data:
                if tunnel.get('name') == tunnel_name:
                    tunnel_id = tunnel.get('id')
                    break
            
            if not tunnel_id:
                print(f"{Colors.RED}Error: Could not find tunnel ID for '{tunnel_name}'{Colors.ENDC}")
                return False
            
            # Create config file for the tunnel
            config_path = self.config_dir / f"{tunnel_name}.yml"
            config_content = f"""tunnel: {tunnel_name}
credentials-file: {self.config_dir}/{tunnel_id}.json
origincert: {self.cert_file if self.cert_file else str(self.config_dir / "cert.pem")}

ingress:
  - hostname: {url}
    service: http://localhost:{port}
  - service: http_status:404
"""
            
            with open(config_path, 'w') as f:
                f.write(config_content)
            print(f"{Colors.GREEN}✓ Created config file: {config_path}{Colors.ENDC}")
            
            # Try to route the tunnel DNS
            print(f"{Colors.CYAN}Attempting to create DNS route for {url}...{Colors.ENDC}")
            cmd = ["cloudflared", "tunnel"]
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            cmd.extend(["route", "dns", tunnel_name, url])
            
            dns_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            # Check if DNS routing succeeded and to which domain
            dns_success = False
            if dns_result.returncode == 0:
                print(f"{Colors.GREEN}✓ DNS route created{Colors.ENDC}")
                # Check if it was created in the correct domain
                if domain_selection and domain_selection not in dns_result.stdout:
                    print(f"{Colors.YELLOW}Warning: DNS may have been created in a different zone than {domain_selection}{Colors.ENDC}")
                else:
                    dns_success = True
            else:
                print(f"{Colors.YELLOW}Automatic DNS routing failed: {dns_result.stderr}{Colors.ENDC}")
            
            # Provide manual DNS instructions if needed  
            if not dns_success or (domain_selection and domain_selection not in dns_result.stdout):
                if dns_result.returncode == 0:
                    # DNS was created but possibly in wrong zone
                    print(f"{Colors.YELLOW}Note: DNS record may have been created in the wrong zone.{Colors.ENDC}")
                    print(f"{Colors.YELLOW}Please verify in your Cloudflare dashboard.{Colors.ENDC}")
                
                print(f"\n{Colors.BOLD}{Colors.YELLOW}Manual DNS Setup Required:{Colors.ENDC}")
                print(f"Please add the following DNS record in your Cloudflare dashboard:\n")
                print(f"  Domain: {Colors.CYAN}{domain_selection or 'your-domain.com'}{Colors.ENDC}")
                print(f"  Type: {Colors.GREEN}CNAME{Colors.ENDC}")
                print(f"  Name: {Colors.GREEN}{url.split('.')[0]}{Colors.ENDC}")
                print(f"  Target: {Colors.GREEN}{tunnel_id}.cfargotunnel.com{Colors.ENDC}")
                print(f"  Proxy: {Colors.GREEN}Enabled (orange cloud){Colors.ENDC}")
                print(f"  TTL: {Colors.GREEN}Auto{Colors.ENDC}\n")
                
                # Always show manual instructions when domain is specified
                dns_success = False
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}Tunnel '{tunnel_name}' created successfully!{Colors.ENDC}")
            print(f"Configuration:")
            print(f"  Local port: {port}")
            print(f"  Public URL: https://{url}")
            print(f"  Config file: {config_path}")
            
            # Auto-start the tunnel if requested
            if auto_start:
                print(f"\n{Colors.CYAN}Starting tunnel...{Colors.ENDC}")
                if self.start_tunnel(tunnel_name, str(config_path)):
                    print(f"\n{Colors.GREEN}✓ Tunnel is now active and running!{Colors.ENDC}")
                    print(f"Your application at localhost:{port} is now accessible at https://{url}")
                else:
                    print(f"\n{Colors.YELLOW}Tunnel created but failed to start automatically.{Colors.ENDC}")
                    print(f"To start manually, run: {Colors.CYAN}./tunnel-manager.py start {tunnel_name}{Colors.ENDC}")
            else:
                print(f"\nTo start the tunnel, run: {Colors.CYAN}./tunnel-manager.py start {tunnel_name}{Colors.ENDC}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error creating tunnel: {e}{Colors.ENDC}")
            if e.stderr:
                print(f"{Colors.RED}Error details: {e.stderr}{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"{Colors.RED}Error creating tunnel: {e}{Colors.ENDC}")
            return False
    
    def delete_tunnel(self, tunnel_name: str, force: bool = False) -> bool:
        """Delete a tunnel and its associated files"""
        try:
            # Check if tunnel exists
            tunnels = self.list_tunnels()
            tunnel_exists = any(t.get('name') == tunnel_name for t in tunnels)
            
            if not tunnel_exists:
                print(f"{Colors.YELLOW}Tunnel '{tunnel_name}' does not exist{Colors.ENDC}")
                return False
            
            # Check if tunnel is running
            running, pid = self.is_tunnel_running(tunnel_name)
            if running:
                if not force:
                    confirm = input(f"{Colors.YELLOW}Tunnel '{tunnel_name}' is currently running. Stop and delete? (y/N): {Colors.ENDC}").strip().lower()
                    if confirm != 'y':
                        print("Deletion cancelled.")
                        return False
                
                print(f"{Colors.CYAN}Stopping tunnel '{tunnel_name}'...{Colors.ENDC}")
                self.stop_tunnel(tunnel_name)
                time.sleep(2)  # Give it time to stop
            
            # Confirm deletion if not forced
            if not force:
                confirm = input(f"{Colors.YELLOW}Are you sure you want to delete tunnel '{tunnel_name}'? This cannot be undone. (y/N): {Colors.ENDC}").strip().lower()
                if confirm != 'y':
                    print("Deletion cancelled.")
                    return False
            
            # Delete the tunnel
            print(f"{Colors.CYAN}Deleting tunnel '{tunnel_name}'...{Colors.ENDC}")
            cmd = ["cloudflared", "tunnel"]
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            cmd.extend(["delete", "-f", tunnel_name])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            print(f"{Colors.GREEN}✓ Deleted tunnel '{tunnel_name}'{Colors.ENDC}")
            
            # Clean up config file
            config_path = self.config_dir / f"{tunnel_name}.yml"
            if config_path.exists():
                config_path.unlink()
                print(f"{Colors.GREEN}✓ Removed config file: {config_path}{Colors.ENDC}")
            
            # Clean up log file if exists
            log_file = self.get_log_file(tunnel_name)
            if log_file.exists():
                log_file.unlink()
                print(f"{Colors.GREEN}✓ Removed log file: {log_file}{Colors.ENDC}")
            
            # Clean up PID file if exists
            pid_file = self.get_pid_file(tunnel_name)
            if pid_file.exists():
                pid_file.unlink()
                print(f"{Colors.GREEN}✓ Removed PID file: {pid_file}{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}Tunnel '{tunnel_name}' deleted successfully!{Colors.ENDC}")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"{Colors.RED}Error deleting tunnel: {e}{Colors.ENDC}")
            if e.stderr:
                print(f"{Colors.RED}Error details: {e.stderr}{Colors.ENDC}")
            return False
        except Exception as e:
            print(f"{Colors.RED}Error deleting tunnel: {e}{Colors.ENDC}")
            return False
    
    def update_tunnel(self, tunnel_name: str, port: Optional[int] = None, url: Optional[str] = None, restart: bool = True) -> bool:
        """Update tunnel configuration (port and/or URL)"""
        try:
            # Check if tunnel exists
            tunnels = self.list_tunnels()
            tunnel_exists = any(t.get('name') == tunnel_name for t in tunnels)
            
            if not tunnel_exists:
                print(f"{Colors.YELLOW}Tunnel '{tunnel_name}' does not exist{Colors.ENDC}")
                return False
            
            if not port and not url:
                print(f"{Colors.YELLOW}No updates specified. Use -p for port or -u for URL.{Colors.ENDC}")
                return False
            
            # Check if config file exists
            config_path = self.config_dir / f"{tunnel_name}.yml"
            if not config_path.exists():
                print(f"{Colors.YELLOW}Config file not found for tunnel '{tunnel_name}'{Colors.ENDC}")
                print(f"Expected at: {config_path}")
                return False
            
            # Read current config
            with open(config_path, 'r') as f:
                config_content = f.read()
            
            # Parse current values
            import re
            current_port = None
            current_url = None
            
            # Extract current port
            port_match = re.search(r'service:\s*http://localhost:(\d+)', config_content)
            if port_match:
                current_port = int(port_match.group(1))
            
            # Extract current URL
            url_match = re.search(r'hostname:\s*([^\s]+)', config_content)
            if url_match:
                current_url = url_match.group(1)
            
            # Prepare updates
            new_port = port if port else current_port
            new_url = url if url else current_url
            
            print(f"\n{Colors.CYAN}Updating tunnel '{tunnel_name}'...{Colors.ENDC}")
            
            if port and current_port != port:
                print(f"  Port: {current_port} → {port}")
            
            if url and current_url != url:
                print(f"  URL: {current_url} → {url}")
                # Need to update DNS routing
                print(f"{Colors.CYAN}Updating DNS route to {url}...{Colors.ENDC}")
                
                # First, remove the old route
                if current_url:
                    try:
                        cmd = ["cloudflared", "tunnel"]
                        if self.cert_file:
                            cmd.extend(["--origincert", self.cert_file])
                        cmd.extend(["route", "dns", "--overwrite-dns", tunnel_name, url])
                        
                        subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            check=True
                        )
                        print(f"{Colors.GREEN}✓ DNS route updated to {url}{Colors.ENDC}")
                    except subprocess.CalledProcessError as e:
                        print(f"{Colors.YELLOW}Warning: Could not update DNS route: {e}{Colors.ENDC}")
            
            # Get tunnel ID for the config
            tunnel_id = None
            cmd = ["cloudflared", "tunnel"]
            if self.cert_file:
                cmd.extend(["--origincert", self.cert_file])
            cmd.extend(["list", "--output", "json"])
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            tunnels_data = json.loads(result.stdout)
            for tunnel in tunnels_data:
                if tunnel.get('name') == tunnel_name:
                    tunnel_id = tunnel.get('id')
                    break
            
            if not tunnel_id:
                print(f"{Colors.RED}Error: Could not find tunnel ID for '{tunnel_name}'{Colors.ENDC}")
                return False
            
            # Update config file
            new_config_content = f"""tunnel: {tunnel_name}
credentials-file: {self.config_dir}/{tunnel_id}.json
origincert: {self.cert_file if self.cert_file else str(self.config_dir / "cert.pem")}

ingress:
  - hostname: {new_url}
    service: http://localhost:{new_port}
  - service: http_status:404
"""
            
            # Check if tunnel is running
            was_running, _ = self.is_tunnel_running(tunnel_name)
            
            # Stop tunnel if running and restart requested
            if was_running and restart:
                print(f"{Colors.CYAN}Stopping tunnel for config update...{Colors.ENDC}")
                self.stop_tunnel(tunnel_name)
                time.sleep(2)
            
            # Write new config
            with open(config_path, 'w') as f:
                f.write(new_config_content)
            print(f"{Colors.GREEN}✓ Updated config file: {config_path}{Colors.ENDC}")
            
            # Restart if was running and restart requested
            if was_running and restart:
                print(f"{Colors.CYAN}Restarting tunnel...{Colors.ENDC}")
                if self.start_tunnel(tunnel_name, str(config_path)):
                    print(f"{Colors.GREEN}✓ Tunnel restarted successfully{Colors.ENDC}")
                else:
                    print(f"{Colors.YELLOW}Failed to restart tunnel. Please start manually.{Colors.ENDC}")
            
            print(f"\n{Colors.BOLD}{Colors.GREEN}Tunnel '{tunnel_name}' updated successfully!{Colors.ENDC}")
            print(f"Configuration:")
            print(f"  Local port: {new_port}")
            print(f"  Public URL: https://{new_url}")
            
            return True
            
        except Exception as e:
            print(f"{Colors.RED}Error updating tunnel: {e}{Colors.ENDC}")
            return False

def main():
    parser = argparse.ArgumentParser(
        description="Cloudflare Tunnel Manager - Manage tunnels with background process support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                    # List all tunnels with status
  %(prog)s start tunnel-name       # Start a tunnel in background
  %(prog)s stop tunnel-name        # Stop a running tunnel
  %(prog)s restart tunnel-name     # Restart a tunnel
  %(prog)s logs tunnel-name        # Show tunnel logs
  %(prog)s create tunnel-name -p 3000 -u app.example.com   # Create new tunnel
  %(prog)s create tunnel-name -p 3000 -u app.exalted.dev -d exalted.dev  # Specify domain
  %(prog)s update tunnel-name -p 8080     # Update tunnel port
  %(prog)s update tunnel-name -u new.example.com --restart  # Update URL and restart
  %(prog)s delete tunnel-name      # Delete a tunnel
  %(prog)s interactive             # Interactive menu mode
        """
    )
    
    # Global options
    parser.add_argument('--cert', help='Certificate file to use (e.g., exalted-cert.pem or termkit-cert.pem)')
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # List command
    subparsers.add_parser('list', help='List all tunnels with their status')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start a tunnel in background')
    start_parser.add_argument('tunnel', help='Tunnel name')
    start_parser.add_argument('-c', '--config', help='Config file path (optional)')
    
    # Stop command
    stop_parser = subparsers.add_parser('stop', help='Stop a running tunnel')
    stop_parser.add_argument('tunnel', help='Tunnel name')
    
    # Restart command
    restart_parser = subparsers.add_parser('restart', help='Restart a tunnel')
    restart_parser.add_argument('tunnel', help='Tunnel name')
    restart_parser.add_argument('-c', '--config', help='Config file path (optional)')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show tunnel logs')
    logs_parser.add_argument('tunnel', help='Tunnel name')
    logs_parser.add_argument('-n', '--lines', type=int, default=50, help='Number of lines to show (default: 50)')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new tunnel')
    create_parser.add_argument('tunnel', nargs='?', help='Tunnel name (will prompt if not provided)')
    create_parser.add_argument('-p', '--port', type=int, help='Local port of the hosted application')
    create_parser.add_argument('-u', '--url', help='URL to push the tunnel through (e.g., example.com or subdomain.example.com)')
    create_parser.add_argument('-d', '--domain', help='Domain to create DNS record in (e.g., example.com)')
    create_parser.add_argument('--no-start', action='store_true', help='Do not automatically start the tunnel after creation')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update tunnel configuration')
    update_parser.add_argument('tunnel', help='Tunnel name to update')
    update_parser.add_argument('-p', '--port', type=int, help='New local port (optional)')
    update_parser.add_argument('-u', '--url', help='New URL (optional)')
    update_parser.add_argument('--restart', action='store_true', help='Restart tunnel after update if running')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a tunnel')
    delete_parser.add_argument('tunnel', nargs='?', help='Tunnel name to delete (will show list if not provided)')
    delete_parser.add_argument('-f', '--force', action='store_true', help='Force delete without confirmation')
    
    # Interactive mode
    subparsers.add_parser('interactive', help='Interactive menu mode')
    
    args = parser.parse_args()
    
    # Handle cert file - if provided without path, assume it's in .cloudflared
    cert_file = None
    if args.cert:
        if '/' not in args.cert:
            cert_file = str(Path.home() / ".cloudflared" / args.cert)
        else:
            cert_file = args.cert
    
    manager = TunnelManager(cert_file=cert_file)
    
    if not args.command or args.command == 'list':
        manager.show_status()
    
    elif args.command == 'start':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        manager.start_tunnel(args.tunnel, args.config)
    
    elif args.command == 'stop':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        manager.stop_tunnel(args.tunnel)
    
    elif args.command == 'restart':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        manager.restart_tunnel(args.tunnel, args.config)
    
    elif args.command == 'logs':
        manager.tail_logs(args.tunnel, args.lines)
    
    elif args.command == 'create':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        
        # Interactive prompts for missing values
        tunnel_name = args.tunnel
        if not tunnel_name:
            tunnel_name = input(f"{Colors.BOLD}Enter tunnel name: {Colors.ENDC}").strip()
            if not tunnel_name:
                print(f"{Colors.RED}Tunnel name is required{Colors.ENDC}")
                sys.exit(1)
        
        port = args.port
        if not port:
            port_str = input(f"{Colors.BOLD}Enter local port number: {Colors.ENDC}").strip()
            if not port_str.isdigit():
                print(f"{Colors.RED}Invalid port number{Colors.ENDC}")
                sys.exit(1)
            port = int(port_str)
        
        url = args.url
        if not url:
            url = input(f"{Colors.BOLD}Enter URL (e.g., app.example.com): {Colors.ENDC}").strip()
            if not url:
                print(f"{Colors.RED}URL is required{Colors.ENDC}")
                sys.exit(1)
        
        # Domain selection
        domain = args.domain
        if not domain:
            # Extract suggested domain from URL
            import re
            suggested_domain = None
            domain_match = re.search(r'([^.]+\.[^.]+)$', url)
            if domain_match:
                suggested_domain = domain_match.group(1)
            
            print(f"\n{Colors.BOLD}Select domain for DNS record:{Colors.ENDC}")
            print(f"Common domains: termkit.dev, exalted.dev, quale.app")
            if suggested_domain:
                domain = input(f"{Colors.BOLD}Enter domain (default: {suggested_domain}): {Colors.ENDC}").strip()
                if not domain:
                    domain = suggested_domain
            else:
                domain = input(f"{Colors.BOLD}Enter domain: {Colors.ENDC}").strip()
        
        # Auto-start prompt
        if not args.no_start:
            auto_start = input(f"{Colors.BOLD}Start tunnel after creation? (Y/n): {Colors.ENDC}").strip().lower()
            auto_start = auto_start != 'n'
        else:
            auto_start = False
        
        manager.create_tunnel(tunnel_name, port, url, auto_start=auto_start, domain_selection=domain)
    
    elif args.command == 'update':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        manager.update_tunnel(args.tunnel, port=args.port, url=args.url, restart=args.restart)
    
    elif args.command == 'delete':
        if not select_certificate_interactive(manager):
            sys.exit(1)
        
        # Show available tunnels if not specified
        tunnel_name = args.tunnel
        if not tunnel_name:
            tunnels = manager.list_tunnels()
            if not tunnels:
                print(f"{Colors.YELLOW}No tunnels available to delete{Colors.ENDC}")
                sys.exit(0)
            
            print(f"\n{Colors.BOLD}Available tunnels:{Colors.ENDC}")
            for i, tunnel in enumerate(tunnels, 1):
                status = "Running" if manager.is_tunnel_running(tunnel['name'])[0] else "Stopped"
                print(f"  {i}. {tunnel['name']} ({status})")
            
            choice = input(f"\n{Colors.BOLD}Select tunnel to delete (number or name): {Colors.ENDC}").strip()
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(tunnels):
                    tunnel_name = tunnels[idx]['name']
                else:
                    print(f"{Colors.RED}Invalid selection{Colors.ENDC}")
                    sys.exit(1)
            except ValueError:
                tunnel_name = choice
        
        manager.delete_tunnel(tunnel_name, force=args.force)
    
    elif args.command == 'interactive':
        # For interactive mode, create manager without auto-selecting cert if not specified
        if not args.cert:
            manager = TunnelManager(auto_select_cert=False)
        interactive_menu(manager)
    
    else:
        parser.print_help()

def select_certificate_interactive(manager: TunnelManager) -> bool:
    """Interactive certificate selection. Returns True if cert was selected."""
    if manager.cert_file:
        return True  # Already have a cert

    cert_files = list((Path.home() / ".cloudflared").glob("*-cert.pem"))

    if not cert_files:
        print(f"{Colors.RED}No certificate files found in ~/.cloudflared/{Colors.ENDC}")
        print(f"Please run: {Colors.CYAN}cloudflared tunnel login{Colors.ENDC}")
        return False
    
    if len(cert_files) == 1:
        manager.cert_file = str(cert_files[0])
        print(f"{Colors.GREEN}Using certificate: {cert_files[0].name}{Colors.ENDC}")
        return True
    
    # Multiple certs - ask user to select
    print(f"\n{Colors.BOLD}Available certificate files:{Colors.ENDC}")
    for i, cert in enumerate(cert_files, 1):
        print(f"  {i}. {cert.name}")
    
    while True:
        choice = input(f"\n{Colors.BOLD}Select certificate (1-{len(cert_files)}): {Colors.ENDC}").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(cert_files):
                manager.cert_file = str(cert_files[idx])
                print(f"{Colors.GREEN}Using certificate: {cert_files[idx].name}{Colors.ENDC}")
                return True
            else:
                print(f"{Colors.RED}Invalid selection{Colors.ENDC}")
        except ValueError:
            print(f"{Colors.RED}Please enter a number{Colors.ENDC}")

def interactive_menu(manager: TunnelManager):
    """Interactive menu for tunnel management"""
    # If no cert was specified, ask user to select
    if not select_certificate_interactive(manager):
        return
    
    while True:
        print(f"\n{Colors.BOLD}{Colors.CYAN}=== Cloudflare Tunnel Manager ==={Colors.ENDC}")
        print("1. List all tunnels")
        print("2. Start a tunnel")
        print("3. Stop a tunnel")
        print("4. Restart a tunnel")
        print("5. View tunnel logs")
        print("6. Create a new tunnel")
        print("7. Update a tunnel")
        print("8. Delete a tunnel")
        print("9. Exit")
        
        try:
            choice = input(f"\n{Colors.BOLD}Select option (1-9): {Colors.ENDC}").strip()
            
            if choice == '1':
                manager.show_status()
            
            elif choice == '2':
                tunnels = manager.list_tunnels()
                if not tunnels:
                    print(f"{Colors.YELLOW}No tunnels available{Colors.ENDC}")
                    continue
                
                print(f"\n{Colors.BOLD}Available tunnels:{Colors.ENDC}")
                for i, tunnel in enumerate(tunnels, 1):
                    print(f"  {i}. {tunnel['name']}")
                
                tunnel_choice = input(f"\n{Colors.BOLD}Enter tunnel number or name: {Colors.ENDC}").strip()
                
                try:
                    idx = int(tunnel_choice) - 1
                    if 0 <= idx < len(tunnels):
                        tunnel_name = tunnels[idx]['name']
                    else:
                        print(f"{Colors.RED}Invalid selection{Colors.ENDC}")
                        continue
                except ValueError:
                    tunnel_name = tunnel_choice
                
                config = input(f"{Colors.BOLD}Config file path (press Enter to skip): {Colors.ENDC}").strip()
                manager.start_tunnel(tunnel_name, config if config else None)
            
            elif choice == '3':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name to stop: {Colors.ENDC}").strip()
                if tunnel_name:
                    manager.stop_tunnel(tunnel_name)
            
            elif choice == '4':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name to restart: {Colors.ENDC}").strip()
                if tunnel_name:
                    config = input(f"{Colors.BOLD}Config file path (press Enter to skip): {Colors.ENDC}").strip()
                    manager.restart_tunnel(tunnel_name, config if config else None)
            
            elif choice == '5':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name: {Colors.ENDC}").strip()
                if tunnel_name:
                    lines = input(f"{Colors.BOLD}Number of lines (default 50): {Colors.ENDC}").strip()
                    manager.tail_logs(tunnel_name, int(lines) if lines.isdigit() else 50)
            
            elif choice == '6':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name for the new tunnel: {Colors.ENDC}").strip()
                if not tunnel_name:
                    print(f"{Colors.RED}Tunnel name is required{Colors.ENDC}")
                    continue
                
                port_str = input(f"{Colors.BOLD}Enter local port number: {Colors.ENDC}").strip()
                if not port_str.isdigit():
                    print(f"{Colors.RED}Invalid port number{Colors.ENDC}")
                    continue
                port = int(port_str)
                
                url = input(f"{Colors.BOLD}Enter URL (e.g., example.com or subdomain.example.com): {Colors.ENDC}").strip()
                if not url:
                    print(f"{Colors.RED}URL is required{Colors.ENDC}")
                    continue
                
                # Extract domain from URL for suggestion
                import re
                suggested_domain = None
                domain_match = re.search(r'([^.]+\.[^.]+)$', url)
                if domain_match:
                    suggested_domain = domain_match.group(1)
                
                # Ask for domain selection
                print(f"\n{Colors.BOLD}Select domain for DNS record:{Colors.ENDC}")
                print(f"Common domains: termkit.dev, exalted.dev, quale.app")
                if suggested_domain:
                    domain = input(f"{Colors.BOLD}Enter domain (default: {suggested_domain}): {Colors.ENDC}").strip()
                    if not domain:
                        domain = suggested_domain
                else:
                    domain = input(f"{Colors.BOLD}Enter domain: {Colors.ENDC}").strip()
                
                auto_start = input(f"{Colors.BOLD}Start tunnel after creation? (Y/n): {Colors.ENDC}").strip().lower()
                auto_start = auto_start != 'n'
                
                manager.create_tunnel(tunnel_name, port, url, auto_start=auto_start, domain_selection=domain)
            
            elif choice == '7':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name to update: {Colors.ENDC}").strip()
                if not tunnel_name:
                    print(f"{Colors.RED}Tunnel name is required{Colors.ENDC}")
                    continue
                
                # Check if tunnel exists
                tunnels = manager.list_tunnels()
                if not any(t.get('name') == tunnel_name for t in tunnels):
                    print(f"{Colors.RED}Tunnel '{tunnel_name}' does not exist{Colors.ENDC}")
                    continue
                
                # Get current config
                config_path = manager.config_dir / f"{tunnel_name}.yml"
                if config_path.exists():
                    with open(config_path, 'r') as f:
                        config_content = f.read()
                    
                    # Extract current values
                    import re
                    port_match = re.search(r'service:\s*http://localhost:(\d+)', config_content)
                    current_port = int(port_match.group(1)) if port_match else "unknown"
                    
                    url_match = re.search(r'hostname:\s*([^\s]+)', config_content)
                    current_url = url_match.group(1) if url_match else "unknown"
                    
                    print(f"\nCurrent configuration:")
                    print(f"  Port: {current_port}")
                    print(f"  URL: {current_url}")
                
                print(f"\n{Colors.BOLD}Leave blank to keep current value{Colors.ENDC}")
                
                port_str = input(f"{Colors.BOLD}New port number (current: {current_port}): {Colors.ENDC}").strip()
                new_port = int(port_str) if port_str.isdigit() else None
                
                new_url = input(f"{Colors.BOLD}New URL (current: {current_url}): {Colors.ENDC}").strip()
                new_url = new_url if new_url else None
                
                if not new_port and not new_url:
                    print(f"{Colors.YELLOW}No changes specified{Colors.ENDC}")
                    continue
                
                restart = input(f"{Colors.BOLD}Restart tunnel after update? (Y/n): {Colors.ENDC}").strip().lower()
                restart = restart != 'n'
                
                manager.update_tunnel(tunnel_name, port=new_port, url=new_url, restart=restart)
            
            elif choice == '8':
                tunnel_name = input(f"{Colors.BOLD}Enter tunnel name to delete: {Colors.ENDC}").strip()
                if not tunnel_name:
                    print(f"{Colors.RED}Tunnel name is required{Colors.ENDC}")
                    continue
                
                manager.delete_tunnel(tunnel_name, force=False)
            
            elif choice == '9':
                print(f"{Colors.GREEN}Goodbye!{Colors.ENDC}")
                break
            
            else:
                print(f"{Colors.RED}Invalid option{Colors.ENDC}")
        
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}Goodbye!{Colors.ENDC}")
            break
        except Exception as e:
            print(f"{Colors.RED}Error: {e}{Colors.ENDC}")

if __name__ == "__main__":
    main()