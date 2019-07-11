## @next

This directory contains logic that aligns with new project structure.

### Creating new component
Run
```
npm run generate
```
and follow the instructions on screen

We use [atomic design](http://bradfrost.com/blog/post/atomic-web-design/) to organise components into groups. The general rule of thumb is following:
- Use atoms for smallest building blocks (think button or input)
- Use molecules for things that consist of atoms (think input with labels and error/helper text)
- Use organisms for things that consist of molecules and/or atoms that together create a standalone UI block (think login form)
- Use views for page content (think login page)

<b>Use Storybook to create and test your components</b>

In your component directory edit the `stories.tsx` and try to showcase component in different scenarios

To see it in action, run
```
npm run @storybook
```
