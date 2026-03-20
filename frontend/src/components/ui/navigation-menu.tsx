import * as React from "react"
import * as NavigationMenuPrimitive from "@radix-ui/react-navigation-menu"

import { cn } from "@/lib/utils"

function NavigationMenu({ ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Root>) {
  return <NavigationMenuPrimitive.Root {...props} />
}

function NavigationMenuList({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.List>) {
  return (
    <NavigationMenuPrimitive.List
      className={cn("flex space-x-1 bg-transparent p-1", className)}
      {...props}
    />
  )
}

function NavigationMenuItem({ ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Item>) {
  return <NavigationMenuPrimitive.Item {...props} />
}

function NavigationMenuTrigger({ className, children, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Trigger>) {
  return (
    <NavigationMenuPrimitive.Trigger
      className={cn(
        "inline-flex items-center rounded-md px-3 py-1.5 text-sm font-medium hover:bg-accent/50 active:scale-[.98]",
        className
      )}
      {...props}
    >
      {children}
    </NavigationMenuPrimitive.Trigger>
  )
}

function NavigationMenuContent({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Content>) {
  return (
    <NavigationMenuPrimitive.Portal>
      <NavigationMenuPrimitive.Content
        className={cn("bg-popover text-popover-foreground rounded-md p-4 shadow-md", className)}
        {...props}
      />
    </NavigationMenuPrimitive.Portal>
  )
}

function NavigationMenuLink({ className, ...props }: React.ComponentProps<typeof NavigationMenuPrimitive.Link>) {
  return (
    <NavigationMenuPrimitive.Link
      className={cn("block rounded-md px-3 py-2 text-sm hover:bg-accent/50", className)}
      {...props}
    />
  )
}

export {
  NavigationMenu,
  NavigationMenuList,
  NavigationMenuItem,
  NavigationMenuTrigger,
  NavigationMenuContent,
  NavigationMenuLink,
}

export default NavigationMenu
