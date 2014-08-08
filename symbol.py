import sublime, sublime_plugin

class GotoDefinition(sublime_plugin.WindowCommand):
    def goto_location(self, l):
        fname, display_fname, rowcol = l
        row, col = rowcol

        v = self.window.open_file(fname + ":" + str(row) + ":" + str(col), sublime.ENCODED_POSITION)

    def select_entry(self, locations, idx, orig_view, orig_sel):
        if idx >= 0:
            self.goto_location(locations[idx])
        else:
            # TODO: restore sel
            if orig_view:
                self.window.focus_view(orig_view)

    def highlight_entry(self, locations, idx):
        fname, display_fname, rowcol = locations[idx]
        row, col = rowcol

        self.window.open_file(fname + ":" + str(row) + ":" + str(col),
            sublime.TRANSIENT | sublime.ENCODED_POSITION)

    def format_location(self, l):
        fname, display_fname, rowcol = l
        row, col = rowcol

        return display_fname + ":" + str(row)

    def lookup_symbol(self, symbol):
        index_locations = self.window.lookup_symbol_in_index(symbol)
        open_file_locations = self.window.lookup_symbol_in_open_files(symbol)

        def file_in_location_list(fname, locations):
            for l in locations:
                if l[0] == fname:
                    return True
            return False;

        # Combine the two lists, overriding results in the index with results
        # from open files, while trying to preserve the order of the files in
        # the index.
        locations = []
        ofl_ignore = []
        for l in index_locations:
            if file_in_location_list(l[0], open_file_locations):
                if not file_in_location_list(l[0], ofl_ignore):
                    for ofl in open_file_locations:
                        if l[0] == ofl[0]:
                            locations.append(ofl)
                            ofl_ignore.append(ofl)
            else:
                locations.append(l)

        for ofl in open_file_locations:
            if not file_in_location_list(ofl[0], ofl_ignore):
                locations.append(ofl)

        return locations

    def run(self, symbol = None):
        orig_sel = None
        v = self.window.active_view()
        if v:
            orig_sel = [r for r in v.sel()]

        if not symbol and not v:
            return

        if not symbol:
            pt = v.sel()[0]

            symbol = v.substr(v.expand_by_class(pt,
                sublime.CLASS_WORD_START | sublime.CLASS_WORD_END,
                "[]{}()<>:."))
            locations = self.lookup_symbol(symbol)

            if len(locations) == 0:
                symbol = v.substr(v.word(pt))
                locations = self.lookup_symbol(symbol)

        else:
            locations = self.lookup_symbol(symbol)

        if len(locations) == 0:
            sublime.status_message("Unable to find " + symbol)
        elif len(locations) == 1:
            self.goto_location(locations[0])
        else:
            self.window.show_quick_panel(
                [self.format_location(l) for l in locations],
                lambda x: self.select_entry(locations, x, v, orig_sel),
                on_highlight = lambda x: self.highlight_entry(locations, x))
