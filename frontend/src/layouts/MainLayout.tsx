import * as React from "react"
import { MenuIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from "@/components/ui/navigation-menu"
// Use plain anchors here to avoid requiring a Router context when the
// component is rendered outside of the SPA root (server-side pages, previews, etc.).

type Props = {
  children: React.ReactNode
}



export default function MainLayout({ children }: Props) {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="w-full border-b bg-background/50">
        <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
          <div className="flex min-w-0 items-center gap-4 md:gap-6">
            <a href="/rankings" className="flex items-center gap-3">
              <img src="/static/og/logo-720.png" alt="BalonRank logo" className="h-12 w-auto object-contain" />
              <span className="font-semibold text-sm">BalonRank</span>
            </a>
            <NavigationMenu className="hidden flex-none md:flex">
              <NavigationMenuList className="flex-none justify-start">


                <NavigationMenuItem>
                  <NavigationMenuTrigger>FAQs</NavigationMenuTrigger>
                  <NavigationMenuContent>
                    <ul className="w-72">
                      <li>
                        <NavigationMenuLink asChild>
                          <a href="/faqs#points-system">How are the points calculated?</a>
                        </NavigationMenuLink>
                      </li>
                      <li>
                        <NavigationMenuLink asChild>
                          <a href="/faqs#supported-competitions">Which competitions are included?</a>
                        </NavigationMenuLink>
                      </li>
                    </ul>
                  </NavigationMenuContent>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>
          </div>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="outline"
                size="icon"
                className="md:hidden"
                aria-label="Open navigation menu"
              >
                <MenuIcon />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-72 md:hidden">

              <DropdownMenuSeparator />
              <DropdownMenuLabel>FAQs</DropdownMenuLabel>
              <DropdownMenuGroup>
                <DropdownMenuItem asChild>
                  <a href="/faqs#points-system">
                    How are the points calculated?
                  </a>
                </DropdownMenuItem>
                <DropdownMenuItem asChild>
                  <a href="/faqs#supported-competitions">
                    Supported Competitions
                  </a>
                </DropdownMenuItem>
              </DropdownMenuGroup>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl flex-1 px-4 py-6">
        {children}
      </main>
    </div>
  )
}
