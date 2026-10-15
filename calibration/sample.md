# Adjudication sample

Seed 0, up to 30 per code. Mark each `ok` (a real finding) or
`fp` (a false positive). A code above roughly two false positives in
thirty gets a narrower detector, drops to advisory, or is cut.

## NAM101 (26 findings, 26 sampled)

- [ ] `cpython/Lib/test/_test_multiprocessing.py:1860` `task` — contains an assertion, takes no arguments
      `def task(self):`
- [ ] `cpython/Lib/test/support/interpreters/__init__.py:92` `get_main` — contains an assertion, takes no arguments
      `def get_main():`
- [ ] `cpython/Lib/test/support/interpreters/queues.py:293` `get_nowait` — contains an assertion, takes no arguments
      `def get_nowait(self):`
- [ ] `cpython/Lib/test/test_asyncio/test_ssl.py:58` `eof_received` — contains an assertion, takes no arguments
      `def eof_received(self):`
- [ ] `cpython/Lib/test/test_capi/check_config.py:10` `import_singlephase` — contains an assertion, takes no arguments
      `def import_singlephase():`
- [ ] `cpython/Lib/test/test_capi/test_misc.py:1622` `run` — contains an assertion, takes no arguments
      `def run(self):`
- [ ] `cpython/Lib/test/test_finalization.py:102` `check_sanity` — contains an assertion, takes no arguments
      `def check_sanity(self):`
- [ ] `cpython/Lib/test/test_finalization.py:234` `check_sanity` — contains an assertion, takes no arguments
      `def check_sanity(self):`
- [ ] `cpython/Lib/test/test_finalization.py:318` `check_sanity` — contains an assertion, takes no arguments
      `def check_sanity(self):`
- [ ] `cpython/Lib/test/test_ftplib.py:293` `start` — contains an assertion, takes no arguments
      `def start(self):`
- [ ] `cpython/Lib/test/test_ftplib.py:308` `stop` — contains an assertion, takes no arguments
      `def stop(self):`
- [ ] `cpython/Lib/test/test_importlib/extension/test_case_sensitivity.py:16` `find_spec` — contains an assertion, takes no arguments
      `def find_spec(self):`
- [ ] `cpython/Lib/test/test_patma.py:3534` `assertRaises` — contains an assertion, takes no arguments
      `def assertRaises(*_, **__):`
- [ ] `cpython/Lib/test/test_poplib.py:223` `start` — contains an assertion, takes no arguments
      `def start(self):`
- [ ] `cpython/Lib/test/test_poplib.py:239` `stop` — contains an assertion, takes no arguments
      `def stop(self):`
- [ ] `cpython/Lib/test/test_statistics.py:1630` `prepare_data` — contains an assertion, takes no arguments
      `def prepare_data(self):`
- [ ] `cpython/Lib/test/test_xml_etree_c.py:258` `install_tests` — contains an assertion, takes no arguments
      `def install_tests():`
- [ ] `pydantic/pydantic-core/tests/validators/test_enums.py:467` `support_custom_new_method` — contains an assertion, takes no arguments
      `def support_custom_new_method() -> None:`
- [ ] `pydantic/pydantic-core/tests/validators/test_model_fields.py:714` `get_int_key` — contains an assertion, takes no arguments
      `def get_int_key():`
- [ ] `pydantic/pydantic-core/tests/validators/test_model_fields.py:733` `get_custom_getitem` — contains an assertion, takes no arguments
      `def get_custom_getitem():`
- [ ] `pydantic/pydantic-core/tests/validators/test_typed_dict.py:586` `get_int_key` — contains an assertion, takes no arguments
      `def get_int_key():`
- [ ] `pydantic/pydantic-core/tests/validators/test_typed_dict.py:605` `get_custom_getitem` — contains an assertion, takes no arguments
      `def get_custom_getitem():`
- [ ] `pydantic/pydantic-core/tests/validators/test_uuid.py:233` `uuid_safety_unknown` — contains an assertion, takes no arguments
      `def uuid_safety_unknown():`
- [ ] `pydantic/tests/test_validate_call.py:70` `validate_bare_none` — contains an assertion, takes no arguments
      `def validate_bare_none() -> None:`
- [ ] `pytest/testing/code/test_source.py:663` `XXX_test_expression_multiline` — contains an assertion, takes no arguments
      `def XXX_test_expression_multiline() -> None:`
- [ ] `rich/tests/test_table.py:16` `render_tables` — contains an assertion, takes no arguments
      `def render_tables():`

## NAM102 (10 findings, 10 sampled)

- [ ] `cpython/Lib/_pyio.py:2104` `write_through` — @property, 'write' is predominantly a verb
      `def write_through(self):`
- [ ] `cpython/Lib/ssl.py:662` `verify_flags` — @property, 'verify' is predominantly a verb
      `def verify_flags(self):`
- [ ] `cpython/Lib/ssl.py:670` `verify_mode` — @property, 'verify' is predominantly a verb
      `def verify_mode(self):`
- [ ] `pydantic/pydantic-core/python/pydantic_core/core_schema.py:140` `include` — @property, 'include' is predominantly a verb
      `def include(self) -> IncExCall:`
- [ ] `pytest/src/_pytest/raises.py:457` `fail_reason` — @property, 'fail' is predominantly a verb
      `def fail_reason(self) -> str | None:`
- [ ] `pytest/testing/test_compat.py:83` `raise_baseexception` — @property, 'raise' is predominantly a verb
      `def raise_baseexception(self):`
- [ ] `pytest/testing/test_compat.py:87` `raise_exception` — @property, 'raise' is predominantly a verb
      `def raise_exception(self):`
- [ ] `pytest/testing/test_compat.py:91` `raise_fail_outcome` — @property, 'raise' is predominantly a verb
      `def raise_fail_outcome(self):`
- [ ] `pytest/testing/test_junitxml.py:126` `get_unique_child` — @property, 'get' is predominantly a verb
      `def get_unique_child(self) -> DomNode:`
- [ ] `rich/rich/table.py:286` `expand` — @property, 'expand' is predominantly a verb
      `def expand(self) -> bool:`

## NAM103 (11 findings, 11 sampled)

- [ ] `cpython/Lib/idlelib/editor.py:1295` `is_char_in_string` — returns 1
      `def is_char_in_string(self, text_index):`
- [ ] `cpython/Lib/idlelib/runscript.py:48` `check_module_event` — returns 'break'
      `def check_module_event(self, event):`
- [ ] `cpython/Lib/optparse.py:1394` `check_values` — returns (values, args)
      `def check_values(self, values, args):`
- [ ] `cpython/Lib/subprocess.py:404` `check_call` — returns 0
      `def check_call(*popenargs, **kwargs):`
- [ ] `cpython/Lib/test/test_asyncgen.py:806` `check_anext_returning_iterator` — returns 'completed'
      `async def check_anext_returning_iterator(self, aiter_class):`
- [ ] `cpython/Lib/test/test_compile.py:1520` `check_positions_against_ast` — returns (code, ast_tree)
      `def check_positions_against_ast(self, snippet):`
- [ ] `cpython/Lib/test/test_patma.py:30` `check_sequence_then_mapping` — returns 'map'
      `def check_sequence_then_mapping(x):`
- [ ] `cpython/Lib/test/test_patma.py:38` `check_mapping_then_sequence` — returns 'seq'
      `def check_mapping_then_sequence(x):`
- [ ] `cpython/Lib/test/test_unittest/test_loader.py:636` `check_deferred_error` — returns (error, test)
      `def check_deferred_error(self, loader, suite):`
- [ ] `cpython/Lib/test/test_venv.py:48` `check_output` — returns (out, err)
      `def check_output(cmd, encoding=None):`
- [ ] `pytest/src/_pytest/capture.py:765` `is_capturing` — annotated -> str | bool
      `def is_capturing(self) -> str | bool:`

## NAM104 (58 findings, 30 sampled)

- [ ] `cpython/Lib/bdb.py:427` `set_break` — returns 'Line %s:%d does not exist' % (filename, lineno)
      `def set_break(self, filename, lineno, temporary=False, cond=None,`
- [ ] `cpython/Lib/bdb.py:484` `clear_bpbynumber` — returns str(err)
      `def clear_bpbynumber(self, arg):`
- [ ] `cpython/Lib/bdb.py:497` `clear_all_file_breaks` — returns 'There are no breakpoints in %s' % filename
      `def clear_all_file_breaks(self, filename):`
- [ ] `cpython/Lib/bdb.py:512` `clear_all_breaks` — returns 'There are no breakpoints'
      `def clear_all_breaks(self):`
- [ ] `cpython/Lib/doctest.py:2239` `set_unittest_reportflags` — returns old
      `def set_unittest_reportflags(flags):`
- [ ] `cpython/Lib/functools.py:36` `update_wrapper` — returns wrapper
      `def update_wrapper(wrapper,`
- [ ] `cpython/Lib/idlelib/config.py:829` `save_all` — returns changed
      `def save_all(self):`
- [ ] `cpython/Lib/idlelib/configdialog.py:2047` `set_extension_value` — returns self.ext_userCfg.SetOption(section, name, value)
      `def set_extension_value(self, section, opt):`
- [ ] `cpython/Lib/idlelib/debugger_r.py:108` `set_break` — returns msg
      `def set_break(self, filename, lineno):`
- [ ] `cpython/Lib/idlelib/debugger_r.py:112` `clear_break` — returns msg
      `def clear_break(self, filename, lineno):`
- [ ] `cpython/Lib/idlelib/debugger_r.py:335` `clear_break` — returns msg
      `def clear_break(self, filename, lineno):`
- [ ] `cpython/Lib/idlelib/debugger_r.py:339` `clear_all_file_breaks` — returns msg
      `def clear_all_file_breaks(self, filename):`
- [ ] `cpython/Lib/idlelib/editor.py:1119` `close_event` — returns 'break'
      `def close_event(self, event):`
- [ ] `cpython/Lib/idlelib/filelist.py:52` `close_all_callback` — returns 'break'
      `def close_all_callback(self, *args, **kwds):`
- [ ] `cpython/Lib/idlelib/iomenu.py:301` `print_window` — returns 'break'
      `def print_window(self, event):`
- [ ] `cpython/Lib/idlelib/undo.py:195` `save_marks` — returns marks
      `def save_marks(self, text):`
- [ ] `cpython/Lib/test/test_bdb.py:107` `set_break` — returns res
      `def set_break(self, filename, lineno, temporary=False, cond=None,`
- [ ] `cpython/Lib/test/test_importlib/test_abc.py:655` `set_data` — returns path == self.bytecode_path
      `def set_data(self, path, data):`
- [ ] `cpython/Lib/turtledemo/__main__.py:274` `update_mousewheel` — returns self.increase_size()
      `def update_mousewheel(self, event):`
- [ ] `httpx/tests/test_auth.py:107` `set_cookies` — returns httpx.Response(content=b'Auth required', status_code=401, headers=headers)
      `def set_cookies(request: httpx.Request) -> httpx.Response:`
- [ ] `pydantic/docs/plugins/main.py:201` `insert_json_output` — returns re.sub('(^ *```)([^\\n]*?output="json"[^\\n]*?\\n)(.+?)\\1', replace_json, markdown, flags=re.M | re.S)
      `def insert_json_output(markdown: str) -> str:`
- [ ] `pydantic/pydantic/_internal/_validate_call.py:29` `update_wrapper_attributes` — returns wrapper_function
      `def update_wrapper_attributes(wrapped: ValidateCallSupportedTypes, wrapper: Callable[..., Any]):`
- [ ] `pydantic/pydantic/deprecated/decorator.py:145` `init_model_instance` — returns self.model(**values)
      `def init_model_instance(self, *args: Any, **kwargs: Any) -> BaseModel:`
- [ ] `pydantic/pydantic/v1/decorator.py:128` `init_model_instance` — returns self.model(**values)
      `def init_model_instance(self, *args: Any, **kwargs: Any) -> BaseModel:`
- [ ] `pydantic/pydantic/v1/mypy.py:772` `set_values_dict` — returns {k: v for k, v in self.__dict__.items() if v is not None}
      `def set_values_dict(self) -> Dict[str, Any]:`
- [ ] `pytest/src/_pytest/fixtures.py:2403` `show_fixtures_per_test` — returns wrap_session(config, _show_fixtures_per_test)
      `def show_fixtures_per_test(config: Config) -> int | ExitCode:`
- [ ] `rich/rich/cells.py:299` `set_cell_size` — returns text
      `def set_cell_size(text: str, total: int, unicode_version: str = "auto") -> str:`
- [ ] `rich/rich/segment.py:426` `set_shape` — returns shaped_lines
      `def set_shape(`
- [ ] `rich/rich/style.py:649` `clear_meta_and_links` — returns style
      `def clear_meta_and_links(self) -> "Style":`
- [ ] `rich/rich/style.py:671` `update_link` — returns style
      `def update_link(self, link: Optional[str] = None) -> "Style":`

## NAM105 (27 findings, 27 sampled)

- [ ] `click/src/click/core.py:1184` `format_usage` — no return carries a value
      `def format_usage(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:1284` `format_help` — no return carries a value
      `def format_help(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:1303` `format_help_text` — no return carries a value
      `def format_help_text(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:1321` `format_options` — no return carries a value
      `def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:1333` `format_arguments` — no return carries a value
      `def format_arguments(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:1346` `format_epilog` — no return carries a value
      `def format_epilog(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:2002` `format_options` — no return carries a value
      `def format_options(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `click/src/click/core.py:2006` `format_commands` — no return carries a value
      `def format_commands(self, ctx: Context, formatter: HelpFormatter) -> None:`
- [ ] `cpython/Lib/idlelib/configdialog.py:846` `get_color` — no return carries a value
      `def get_color(self):`
- [ ] `cpython/Lib/idlelib/configdialog.py:1371` `get_new_keys` — no return carries a value
      `def get_new_keys(self):`
- [ ] `cpython/Lib/idlelib/replace.py:86` `find_it` — no return carries a value
      `def find_it(self, event=None):`
- [ ] `cpython/Lib/pickle.py:1598` `get_extension` — no return carries a value
      `def get_extension(self, code):`
- [ ] `cpython/Lib/pstats.py:159` `get_top_level_stats` — no return carries a value
      `def get_top_level_stats(self):`
- [ ] `cpython/Lib/pstats.py:308` `calc_callees` — no return carries a value
      `def calc_callees(self):`
- [ ] `cpython/Lib/test/test_email/test__header_value_parser.py:1038` `get_phrase_cfws_only_raises` — no return carries a value
      `def get_phrase_cfws_only_raises(self):`
- [ ] `cpython/Lib/test/test_email/test_contentmanager.py:21` `get_key_as_get_content_key` — no return carries a value
      `def get_key_as_get_content_key(self, order, key):`
- [ ] `cpython/Lib/test/test_email/test_contentmanager.py:32` `get_key_as_get_content_key_order` — no return carries a value
      `def get_key_as_get_content_key_order(self, order, key):`
- [ ] `cpython/Lib/test/test_email/test_message.py:774` `get_payload_surrogate_as_gh_94606` — no return carries a value
      `def get_payload_surrogate_as_gh_94606(self, msg, expected):`
- [ ] `cpython/Lib/test/test_embed.py:745` `get_expected_config` — no return carries a value
      `def get_expected_config(self, expected_preconfig, expected,`
- [ ] `cpython/Lib/test/test_importlib/test_threaded_import.py:73` `find_spec` — no return carries a value
      `def find_spec(self, name, path=None, target=None):`
- [ ] `cpython/Lib/test/test_importlib/test_threaded_import.py:88` `find_spec` — no return carries a value
      `def find_spec(self, name, path=None, target=None):`
- [ ] `cpython/Lib/test/test_minidom.py:444` `get_empty_nodelist_from_elements_by_tagName_ns_helper` — no return carries a value
      `def get_empty_nodelist_from_elements_by_tagName_ns_helper(self, doc, nsuri,`
- [ ] `flask/src/flask/cli.py:267` `get_version` — no return carries a value
      `def get_version(ctx: click.Context, param: click.Parameter, value: t.Any) -> None:`
- [ ] `pydantic/pydantic-core/tests/validators/test_model_fields.py:714` `get_int_key` — no return carries a value
      `def get_int_key():`
- [ ] `pydantic/pydantic-core/tests/validators/test_model_fields.py:733` `get_custom_getitem` — no return carries a value
      `def get_custom_getitem():`
- [ ] `pydantic/pydantic-core/tests/validators/test_typed_dict.py:586` `get_int_key` — no return carries a value
      `def get_int_key():`
- [ ] `pydantic/pydantic-core/tests/validators/test_typed_dict.py:605` `get_custom_getitem` — no return carries a value
      `def get_custom_getitem():`

## NAM106 (37 findings, 30 sampled)

- [ ] `cpython/Lib/mailbox.py:373` `get_message` — calls open
      `def get_message(self, key):`
- [ ] `cpython/Lib/mailbox.py:388` `get_bytes` — calls open
      `def get_bytes(self, key):`
- [ ] `cpython/Lib/mailbox.py:393` `get_file` — calls open
      `def get_file(self, key):`
- [ ] `cpython/Lib/mailbox.py:1079` `get_message` — calls open
      `def get_message(self, key):`
- [ ] `cpython/Lib/mailbox.py:1125` `get_file` — calls open
      `def get_file(self, key):`
- [ ] `cpython/Lib/mailbox.py:1217` `get_sequences` — calls open
      `def get_sequences(self):`
- [ ] `cpython/Lib/multiprocessing/resource_sharer.py:82` `get_connection` — calls c.send
      `def get_connection(ident):`
- [ ] `cpython/Lib/test/_test_multiprocessing.py:5368` `get_high_socket_fd` — calls socket.socket
      `def get_high_socket_fd(self):`
- [ ] `cpython/Lib/test/test_dtrace.py:189` `get_readelf_version` — calls subprocess.Popen
      `def get_readelf_version():`
- [ ] `cpython/Lib/test/test_dtrace.py:218` `get_readelf_output` — calls subprocess.Popen
      `def get_readelf_output(self):`
- [ ] `cpython/Lib/test/test_faulthandler.py:50` `get_output` — calls open
      `def get_output(self, code, filename=None, fd=None):`
- [ ] `cpython/Lib/test/test_gdb/util.py:159` `get_stack_trace` — calls subprocess._args_from_interpreter_flags
      `def get_stack_trace(self, source=None, script=None,`
- [ ] `cpython/Lib/test/test_plistlib.py:1116` `get_lint_status` — calls subprocess.run
      `def get_lint_status(self):`
- [ ] `cpython/Lib/test/test_shutil.py:3111` `get_files` — calls open
      `def get_files(self):`
- [ ] `cpython/Lib/test/test_socket.py:89` `get_cid` — calls open
      `def get_cid():`
- [ ] `cpython/Lib/test/test_turtle.py:55` `get_cfg_file` — calls open
      `def get_cfg_file(self, cfg_str):`
- [ ] `cpython/Lib/test/test_venv.py:108` `get_text_file_contents` — calls open
      `def get_text_file_contents(self, *args, encoding='utf-8'):`
- [ ] `cpython/Lib/test/test_zoneinfo/data/update_test_data.py:52` `get_zoneinfo_metadata` — calls open
      `def get_zoneinfo_metadata() -> typing.Dict[str, str]:`
- [ ] `cpython/Lib/test/test_zoneinfo/data/update_test_data.py:79` `get_zoneinfo` — calls open
      `def get_zoneinfo(key: str) -> bytes:`
- [ ] `cpython/Lib/urllib/request.py:1463` `get_names` — calls socket.gethostbyname
      `def get_names(self):`
- [ ] `cpython/Lib/wsgiref/simple_server.py:75` `get_environ` — calls urllib.parse.unquote
      `def get_environ(self):`
- [ ] `flask/examples/tutorial/flaskr/blog.py:28` `get_post` — calls fetchone
      `def get_post(id, check_author=True):`
- [ ] `httpx/tests/client/test_cookies.py:8` `get_and_set_cookies` — calls httpx.Response
      `def get_and_set_cookies(request: httpx.Request) -> httpx.Response:`
- [ ] `pydantic/.github/actions/people/people.py:358` `get_graphql_response` — calls requests.post
      `def get_graphql_response(`
- [ ] `pydantic/release/prepare.py:56` `get_notes` — calls requests.post
      `def get_notes(new_version: str) -> str:`
- [ ] `pydantic/release/push.py:20` `get_latest_version_from_changelog` — calls open
      `def get_latest_version_from_changelog() -> str:`
- [ ] `pydantic/release/push.py:30` `get_latest_release_notes_from_changelog` — calls open
      `def get_latest_release_notes_from_changelog() -> str:`
- [ ] `pytest/extra/get_issues.py:13` `get_issues` — calls requests.utils.parse_header_links
      `def get_issues():`
- [ ] `pytest/src/_pytest/assertion/rewrite.py:290` `get_data` — calls open
      `def get_data(self, pathname: str | bytes) -> bytes:`
- [ ] `pytest/src/_pytest/pytester.py:123` `get_open_files` — calls subprocess.run
      `def get_open_files(self) -> list[tuple[str, str]]:`

## NAM107 (232 findings, 30 sampled)

- [ ] `click/examples/imagepipe/imagepipe.py:243` `emboss_cmd` — contains yield
      `def emboss_cmd(images):`
- [ ] `cpython/Lib/difflib.py:833` `compare` — contains yield
      `def compare(self, a, b):`
- [ ] `cpython/Lib/difflib.py:874` `_dump` — contains yield
      `def _dump(self, tag, x, lo, hi):`
- [ ] `cpython/Lib/difflib.py:987` `_fancy_helper` — contains yield
      `def _fancy_helper(self, a, alo, ahi, b, blo, bhi):`
- [ ] `cpython/Lib/difflib.py:2019` `restore` — contains yield
      `def restore(delta, which):`
- [ ] `cpython/Lib/glob.py:63` `_iglob` — contains yield
      `def _iglob(pathname, root_dir, dir_fd, recursive, dironly,`
- [ ] `cpython/Lib/idlelib/idle_test/test_colorizer.py:555` `test_incremental_editing` — contains yield
      `def test_incremental_editing(self):`
- [ ] `cpython/Lib/idlelib/idle_test/test_sidebar.py:512` `test_single_empty_input` — contains yield
      `def test_single_empty_input(self):`
- [ ] `cpython/Lib/idlelib/idle_test/test_sidebar.py:518` `test_single_line_statement` — contains yield
      `def test_single_line_statement(self):`
- [ ] `cpython/Lib/os.py:498` `_fwalk` — contains yield
      `def _fwalk(stack, isbytes, topdown, onerror, follow_symlinks):`
- [ ] `cpython/Lib/pathlib/_local.py:560` `_filter_trailing_slash` — contains yield
      `def _filter_trailing_slash(self, paths):`
- [ ] `cpython/Lib/pprint.py:643` `_wrap_bytes_repr` — contains yield
      `def _wrap_bytes_repr(object, width, allowance):`
- [ ] `cpython/Lib/test/_test_multiprocessing.py:2999` `baz` — contains yield
      `def baz():`
- [ ] `cpython/Lib/test/test_set.py:18` `check_pass_thru` — contains yield
      `def check_pass_thru():`
- [ ] `cpython/Lib/test/test_trace.py:68` `traced_func_generator` — contains yield
      `def traced_func_generator(num):`
- [ ] `cpython/Lib/turtledemo/tree.py:21` `tree` — contains yield
      `def tree(plist, l, a, f):`
- [ ] `httpx/httpx/_auth.py:38` `auth_flow` — contains yield
      `def auth_flow(self, request: Request) -> typing.Generator[Request, Response, None]:`
- [ ] `httpx/tests/models/test_responses.py:22` `async_streaming_body` — contains yield
      `async def async_streaming_body() -> typing.AsyncIterator[bytes]:`
- [ ] `pytest/src/_pytest/_io/pprint.py:198` `_pprint_dict` — contains yield
      `def _pprint_dict(`
- [ ] `pytest/src/_pytest/_io/pprint.py:246` `_pprint_tuple` — contains yield
      `def _pprint_tuple(`
- [ ] `pytest/src/_pytest/assertion/_compare_sequence.py:46` `_compare_eq_sequence` — contains yield
      `def _compare_eq_sequence(`
- [ ] `pytest/src/_pytest/assertion/compare_text.py:14` `_compare_eq_text` — contains yield
      `def _compare_eq_text(`
- [ ] `pytest/src/_pytest/assertion/compare_text.py:31` `_diff_text_block` — contains yield
      `def _diff_text_block(left: str, right: str) -> Iterator[str]:`
- [ ] `pytest/src/_pytest/assertion/util.py:108` `assertrepr_compare` — contains yield
      `def assertrepr_compare(`
- [ ] `pytest/src/_pytest/python.py:715` `collect` — contains yield
      `def collect(self) -> Iterable[nodes.Item | nodes.Collector]:`
- [ ] `pytest/testing/example_scripts/fixtures/custom_item/conftest.py:13` `collect` — contains yield
      `def collect(self):`
- [ ] `rich/rich/layout.py:109` `divide` — contains yield
      `def divide(`
- [ ] `rich/rich/progress_bar.py:126` `_render_pulse` — contains yield
      `def _render_pulse(`
- [ ] `rich/rich/segment.py:608` `remove_color` — contains yield
      `def remove_color(cls, segments: Iterable["Segment"]) -> Iterable["Segment"]:`
- [ ] `rich/rich/text.py:719` `render` — contains yield
      `def render(self, console: "Console", end: str = "") -> Iterable["Segment"]:`

## NAM108 (36 findings, 30 sampled)

- [ ] `click/examples/aliases/aliases.py:25` `write_config` — method of Config
      `def write_config(self, filename):`
- [ ] `click/src/click/_termui_impl.py:696` `get_editor` — method of Editor
      `def get_editor(self) -> str:`
- [ ] `click/src/click/types.py:406` `normalize_choice` — method of Choice
      `def normalize_choice(self, choice: object, ctx: Context | None) -> str:`
- [ ] `click/src/click/types.py:478` `get_invalid_choice_message` — method of Choice
      `def get_invalid_choice_message(self, value: t.Any, ctx: Context | None) -> str:`
- [ ] `cpython/Lib/argparse.py:1689` `add_argument_group` — method of _ArgumentGroup
      `def add_argument_group(self, *args, **kwargs):`
- [ ] `cpython/Lib/argparse.py:1718` `add_mutually_exclusive_group` — method of _MutuallyExclusiveGroup
      `def add_mutually_exclusive_group(self, *args, **kwargs):`
- [ ] `cpython/Lib/email/_header_value_parser.py:719` `stripped_value` — method of Value
      `def stripped_value(self):`
- [ ] `cpython/Lib/email/charset.py:266` `get_output_charset` — method of Charset
      `def get_output_charset(self):`
- [ ] `cpython/Lib/idlelib/codecontext.py:93` `toggle_code_context_event` — method of CodeContext
      `def toggle_code_context_event(self, event=None):`
- [ ] `cpython/Lib/idlelib/codecontext.py:179` `update_code_context` — method of CodeContext
      `def update_code_context(self):`
- [ ] `cpython/Lib/idlelib/format.py:42` `format_paragraph_event` — method of FormatParagraph
      `def format_paragraph_event(self, event, limit=None):`
- [ ] `cpython/Lib/idlelib/history.py:31` `history_next` — method of History
      `def history_next(self, event):`
- [ ] `cpython/Lib/idlelib/history.py:36` `history_prev` — method of History
      `def history_prev(self, event):`
- [ ] `cpython/Lib/idlelib/zoomheight.py:21` `zoom_height_event` — method of ZoomHeight
      `def zoom_height_event(self, event=None):`
- [ ] `cpython/Lib/pdb.py:2151` `help_pdb` — method of Pdb
      `def help_pdb(self):`
- [ ] `cpython/Lib/tkinter/__init__.py:492` `trace_variable` — method of Variable
      `def trace_variable(self, mode, callback):`
- [ ] `cpython/Lib/trace.py:557` `localtrace_trace_and_count` — method of Trace
      `def localtrace_trace_and_count(self, frame, why, arg):`
- [ ] `cpython/Lib/trace.py:576` `localtrace_trace` — method of Trace
      `def localtrace_trace(self, frame, why, arg):`
- [ ] `cpython/Lib/xml/dom/minidom.py:206` `cloneNode` — method of Node
      `def cloneNode(self, deep):`
- [ ] `cpython/Lib/xml/dom/minidom.py:218` `isSameNode` — method of Node
      `def isSameNode(self, other):`
- [ ] `flask/src/flask/sansio/blueprints.py:256` `register_blueprint` — method of Blueprint
      `def register_blueprint(self, blueprint: Blueprint, **options: t.Any) -> None:`
- [ ] `flask/src/flask/views.py:86` `as_view` — method of View
      `def as_view(`
- [ ] `httpx/httpx/_models.py:1101` `extract_cookies` — method of Cookies
      `def extract_cookies(self, response: Response) -> None:`
- [ ] `httpx/httpx/_urls.py:308` `is_absolute_url` — method of URL
      `def is_absolute_url(self) -> bool:`
- [ ] `httpx/httpx/_urls.py:320` `is_relative_url` — method of URL
      `def is_relative_url(self) -> bool:`
- [ ] `pydantic/pydantic/_internal/_generate_schema.py:2804` `unpack_definitions` — method of _Definitions
      `def unpack_definitions(self, schema: core_schema.DefinitionsSchema) -> CoreSchema:`
- [ ] `pytest/src/_pytest/config/__init__.py:1766` `issue_config_time_warning` — method of Config
      `def issue_config_time_warning(self, warning: Warning, stacklevel: int) -> None:`
- [ ] `pytest/src/_pytest/nodes.py:360` `iter_markers_with_node` — method of Node
      `def iter_markers_with_node(`
- [ ] `rich/rich/style.py:564` `get_html_style` — method of Style
      `def get_html_style(self, theme: Optional[TerminalTheme] = None) -> str:`
- [ ] `rich/rich/text.py:1008` `append_text` — method of Text
      `def append_text(self, text: "Text") -> "Text":`
