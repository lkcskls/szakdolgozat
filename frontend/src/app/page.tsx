import { redirect } from "next/navigation";

export default function Home() {
  //átirányítás
  redirect("/login");
}