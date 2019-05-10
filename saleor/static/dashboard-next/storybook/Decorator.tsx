import * as React from "react";

import AppActionContext from "../components/AppLayout/AppActionContext";
import { Provider as DateProvider } from "../components/Date/DateContext";
import { FormProvider } from "../components/Form";
import { MessageManager } from "../components/messages";
import ThemeProvider from "../components/Theme";
import { TimezoneProvider } from "../components/Timezone";

const DecoratorComponent: React.FC<{ story: any }> = ({ story }) => {
  const appActionAnchor = React.useRef<HTMLDivElement>();

  return (
    <FormProvider>
      <DateProvider value={+new Date("2018-08-07T14:30:44+00:00")}>
        <TimezoneProvider value="America/New_York">
          <ThemeProvider isDefaultDark={false}>
            <MessageManager>
              <AppActionContext.Provider value={appActionAnchor}>
                <div
                  style={{
                    display: "flex",
                    flexGrow: 1,
                    padding: 24
                  }}
                >
                  <div style={{ flexGrow: 1 }}>{story}</div>
                </div>
                <div
                  style={{
                    bottom: 0,
                    gridColumn: 2,
                    position: "sticky"
                  }}
                  ref={appActionAnchor}
                />
              </AppActionContext.Provider>
            </MessageManager>
          </ThemeProvider>
        </TimezoneProvider>
      </DateProvider>
    </FormProvider>
  );
};
export const Decorator = storyFn => <DecoratorComponent story={storyFn()} />;
export default Decorator;
