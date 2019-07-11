import { storiesOf } from "@storybook/react";

export const createStory = (name: string = "default") =>
  storiesOf(`@components/atoms/${name}`, module);
