# Developer Documentation

Welcome to the comprehensive developer documentation for the Telegram Group Message Crawler. This documentation provides in-depth technical information for developers integrating or extending the library.

## 📚 Documentation Structure

### Core Concepts
- **[What Is This For?](what_is_this_for.md)** - Understanding the library's purpose and design philosophy
- **[Interfaces and Endpoints](interfaces_and_endpoints.md)** - Complete API reference and method signatures
- **[Summary](summary.md)** - High-level overview and key takeaways

### Integration Guide
- **[Integration Points](integration_points.md)** - Where and how to integrate with your systems
- **[Integration Requirements](integration_requirements.md)** - System requirements and dependencies
- **[Example Usage](example_usage.md)** - Practical code examples and patterns

### Considerations
- **[Limitations](limitations.md)** - Current limitations and constraints
- **[Edge Cases Covered](edge_cases_covered.md)** - How the library handles edge cases
- **[Possible Use Cases](possible_use_cases.md)** - Real-world applications and scenarios

## 🚀 Quick Navigation

### For New Users
1. Start with [What Is This For?](what_is_this_for.md)
2. Review [Integration Requirements](integration_requirements.md)
3. Explore [Example Usage](example_usage.md)

### For Integrators
1. Check [Integration Points](integration_points.md)
2. Understand [Interfaces and Endpoints](interfaces_and_endpoints.md)
3. Review [Edge Cases Covered](edge_cases_covered.md)

### For Advanced Users
1. Study [Limitations](limitations.md)
2. Explore [Possible Use Cases](possible_use_cases.md)
3. Implement custom solutions based on examples

## 🏗️ Architecture Overview

```
tgdata/
├── tgdata.py                  # Main API class
├── connection_engine.py       # Connection management
├── message_engine.py          # Message operations
├── message_tracker_interface.py # Extensible tracking
├── models.py                  # Data models
├── progress.py               # Progress tracking
└── utils.py                  # Utilities
```

## 💡 Key Features

- **Unified API**: Single `TgData` class for all operations
- **Clean Architecture**: Separated engines for different concerns
- **Extensibility**: Interface-based design for custom implementations
- **Performance**: Connection pooling and efficient caching
- **Reliability**: Comprehensive error handling and recovery

## 📝 Code Example

```python
from tgdata import TgData
import asyncio

async def main():
    # Initialize with custom configuration
    tg = TgData(
        connection_pool_size=3,
        enable_deduplication=True
    )
    
    # Get messages with progress tracking
    messages = await tg.get_messages(
        group_id=12345,
        limit=1000,
        with_progress=True
    )
    
    # Process and export
    stats = tg.get_statistics(messages)
    tg.export_messages(messages, "output.csv")

asyncio.run(main())
```

## 🔗 Related Resources

- **Source Code**: Available in the parent directory
- **Examples**: See `src2/examples/` for implementation examples
- **Tests**: Check `src2/smoke_tests/` for test patterns

## 📋 Documentation Maintenance

This documentation reflects the current state of the refactored architecture. Key improvements include:

- Consolidated from dual-class to single unified `TgData` class
- Extracted connection and message handling to specialized engines
- Implemented flexible message tracker interface
- Added comprehensive progress tracking
- Improved error handling and edge case coverage

Last updated: August 2024

## 🤝 Contributing

When extending the library:

1. Follow the existing architecture patterns
2. Implement appropriate interfaces
3. Add comprehensive error handling
4. Include progress tracking where appropriate
5. Document new features

## 📞 Support

For questions or issues:
- Review the documentation thoroughly
- Check edge cases and limitations
- Refer to example implementations
- Test with the smoke test suite

---

*This documentation is part of the Telegram Group Message Crawler project, providing a clean and extensible solution for programmatic access to Telegram group messages.*