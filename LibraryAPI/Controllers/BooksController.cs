using System.Collections.Generic;
using System.Threading.Tasks;
using LibraryAPI.Models;
using LibraryAPI.Services;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;

namespace LibraryAPI.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class BooksController : ControllerBase
    {
        private readonly IBookService _bookService;

        public BooksController(IBookService bookService)
        {
            _bookService = bookService;
        }

        /// <summary>
        /// Public endpoint to retrieve all books
        /// </summary>
        [HttpGet]
        [AllowAnonymous]
        public async Task<ActionResult<IEnumerable<Book>>> GetBooks()
        {
            var books = await _bookService.GetAllBooksAsync();
            return Ok(books);
        }

        /// <summary>
        /// Public endpoint to retrieve a single book by ID
        /// </summary>
        [HttpGet("{id}")]
        [AllowAnonymous]
        public async Task<ActionResult<Book>> GetBook(int id)
        {
            var book = await _bookService.GetBookByIdAsync(id);
            if (book == null)
            {
                return NotFound(new { message = $"Book with ID {id} not found." });
            }
            return Ok(book);
        }

        /// <summary>
        /// Week 6: Public endpoint for AI Tool Calling to check live book availability
        /// </summary>
        [HttpGet("{id}/availability")]
        [AllowAnonymous]
        public async Task<IActionResult> GetBookAvailability(int id)
        {
            var book = await _bookService.GetBookByIdAsync(id);
            if (book == null)
            {
                return NotFound(new { bookId = id, isAvailable = false, message = $"Book with ID {id} was not found." });
            }
            return Ok(new { bookId = id, title = book.Title, isAvailable = book.IsAvailable });
        }

        /// <summary>
        /// Protected endpoint: Requires valid JWT (any authenticated user)
        /// </summary>
        [HttpPost]
        [Authorize]
        public async Task<ActionResult<Book>> CreateBook([FromBody] Book book)
        {
            if (!ModelState.IsValid)
            {
                return BadRequest(ModelState);
            }

            var createdBook = await _bookService.AddBookAsync(book);
            return CreatedAtAction(nameof(GetBook), new { id = createdBook.Id }, createdBook);
        }

        /// <summary>
        /// Protected endpoint: Requires valid JWT (any authenticated user)
        /// </summary>
        [HttpPut("{id}")]
        [Authorize]
        public async Task<IActionResult> UpdateBook(int id, [FromBody] Book book)
        {
            if (id != book.Id)
            {
                return BadRequest(new { message = "ID mismatch between route and body." });
            }

            var result = await _bookService.UpdateBookAsync(book);
            if (!result)
            {
                return NotFound(new { message = $"Book with ID {id} not found." });
            }

            return NoContent();
        }

        /// <summary>
        /// Role-restricted endpoint: Requires valid JWT with Admin role
        /// </summary>
        [HttpDelete("{id}")]
        [Authorize(Roles = "Admin")]
        public async Task<IActionResult> DeleteBook(int id)
        {
            var result = await _bookService.DeleteBookAsync(id);
            if (!result)
            {
                return NotFound(new { message = $"Book with ID {id} not found." });
            }

            return NoContent();
        }
    }
}
