import useLocalStorage from "@saleor/hooks/useLocalStorage";
import { defaultListSettings } from "./../config";
import { Lists, ListSettings } from "./../types";

export default function useListSettings(listName: Lists) {
  const [listSettings, setListSettings] = useLocalStorage(
    "listConfig",
    defaultListSettings
  );
  const updateListSettings = (key: keyof ListSettings, value: any) => {
    setListSettings(settings => ({
      ...settings,
      [listName]: {
        ...settings[listName],
        [key]: value
      }
    }));
  };

  return {
    listSettings,
    updateListSettings
  };
}
