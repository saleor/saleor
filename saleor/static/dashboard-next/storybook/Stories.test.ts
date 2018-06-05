/* eslint-disable */
import initStoryshots from "@storybook/addon-storyshots";
import { configure, render } from "enzyme";
import * as Adapter from "enzyme-adapter-react-16";
import toJSON from "enzyme-to-json";

configure({ adapter: new Adapter() });

initStoryshots({
  configPath: "saleor/static/dashboard-next/storybook/",
  test({ story, context }) {
    const result = render(story.render(context));
    expect(toJSON(result)).toMatchSnapshot();
  }
});
