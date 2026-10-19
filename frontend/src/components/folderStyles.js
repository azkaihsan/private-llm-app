import {
  Folder, FolderOpen, Briefcase, Code, BookOpen, Rocket, Lightbulb, Heart, Star,
  FlaskConical, GraduationCap, Music, Camera, Globe, ShoppingCart, Wrench, Palette
} from 'lucide-react';

export const FOLDER_COLORS = ['', '#ef4444', '#f97316', '#eab308', '#22c55e', '#14b8a6', '#3b82f6', '#6366f1', '#a855f7', '#ec4899', '#94a3b8'];

export const FOLDER_ICONS = {
  folder: Folder, briefcase: Briefcase, code: Code, book: BookOpen, rocket: Rocket, lightbulb: Lightbulb,
  heart: Heart, star: Star, flask: FlaskConical, graduation: GraduationCap, music: Music, camera: Camera,
  globe: Globe, cart: ShoppingCart, wrench: Wrench, palette: Palette,
};

export const folderIcon = (folder, open) => {
  const custom = folder.icon && folder.icon !== 'folder' && FOLDER_ICONS[folder.icon];
  return custom || (open ? FolderOpen : Folder);
};
