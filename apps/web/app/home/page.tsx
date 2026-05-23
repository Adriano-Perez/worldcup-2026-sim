import { redirect } from 'next/navigation';

export default function HomeRoutePage() {
  // Redirect legacy /home to canonical /
  redirect('/');
}
