import createGenerateClassName from "@material-ui/core/styles/createGenerateClassName";
import initStoryshots from "@storybook/addon-storyshots";
// tslint:disable no-submodule-imports
import * as generateRandomKey from "draft-js/lib/generateRandomKey";
import { configure, render } from "enzyme";
import * as Adapter from "enzyme-adapter-react-16";
import toJSON from "enzyme-to-json";

configure({ adapter: new Adapter() });

jest.mock("@material-ui/core/styles/createGenerateClassName");
(createGenerateClassName as any).mockImplementation(
  () => (rule, stylesheet) => {
    return [stylesheet.options.meta, rule.key, "id"].join("-");
  }
);

jest.mock("draft-js/lib/generateRandomKey");
(generateRandomKey as any).mockImplementation(() => "testKey");

initStoryshots({
  configPath: "saleor/static/dashboard-next/storybook/",
  test({ story }) {
    const result = render(story.render() as any);
    expect(toJSON(result)).toMatchSnapshot();
  }
});
