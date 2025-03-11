"use client";
import Image from "next/image";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { ImageIcon } from "lucide-react";

export default function NavBar() {
  const [open, setOpen] = useState(false);

  return (
    <nav className="w-full">
      <div className="flex justify-between items-center px-8 py-2">
        <a href="/">
          <Image src="/logo.png" alt="logo" width={400} height={400}></Image>
        </a>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button variant="default">
              Guide
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-md">
            <DialogHeader>
              <DialogTitle>Guide Information</DialogTitle>
            </DialogHeader>
            <div className="flex justify-center p-6">
              <Image 
                src="/guide.jpeg" 
                alt="Guide" 
                width={750} 
                height={750} 
                className="rounded-md"
              />
            </div>
          </DialogContent>
        </Dialog>
      </div>
      <div className="border-b border-secondary"></div>
    </nav>
  );
}