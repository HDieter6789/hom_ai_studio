import type { LucideIcon } from "lucide-react";
import {
  Boxes,
  Cpu,
  Database,
  FlaskConical,
  LayoutDashboard,
  Library,
  Rocket,
  Settings,
  SlidersHorizontal,
} from "lucide-react";

export interface NavItem {
  label: string;
  href: string;
  icon: LucideIcon;
}

export const NAV_ITEMS: NavItem[] = [
  { label: "Overview", href: "/", icon: LayoutDashboard },
  { label: "Datasets", href: "/datasets", icon: Database },
  { label: "Models", href: "/models", icon: Boxes },
  { label: "Training", href: "/training", icon: SlidersHorizontal },
  { label: "Evaluations", href: "/evaluations", icon: FlaskConical },
  { label: "Registry", href: "/registry", icon: Library },
  { label: "Deployments", href: "/deployments", icon: Rocket },
  { label: "Infrastructure", href: "/infrastructure", icon: Cpu },
  { label: "Settings", href: "/settings", icon: Settings },
];
